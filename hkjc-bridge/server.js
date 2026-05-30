const express = require('express');
const { GraphQLClient } = require('graphql-request');
const { HorseRacingAPI } = require('hkjc-api');

const app = express();
const gql = new GraphQLClient('https://info.cld.hkjc.com/graphql/base/');
const api = new HorseRacingAPI();

const PORT = process.env.NODE_PORT || 3000;

const horseOddsQuery = `
query racing($date: String, $venueCode: String, $oddsTypes: [OddsType], $raceNo: Int) {
  raceMeetings(date: $date, venueCode: $venueCode) {
    pmPools(oddsTypes: $oddsTypes, raceNo: $raceNo) {
      id status sellStatus oddsType lastUpdateTime
      guarantee minTicketCost name_en name_ch
      leg { number races }
      cWinSelections { composite name_ch name_en starters }
      oddsNodes {
        combString oddsValue hotFavourite oddsDropValue
        bankerOdds { combString oddsValue }
      }
    }
  }
}`;

const horsePoolQuery = `
query racing($date: String, $venueCode: String, $oddsTypes: [OddsType], $raceNo: Int) {
  raceMeetings(date: $date, venueCode: $venueCode) {
    totalInvestment
    poolInvs: pmPools(oddsTypes: $oddsTypes, raceNo: $raceNo) {
      id leg { number races }
      status sellStatus oddsType investment mergedPoolId lastUpdateTime
    }
  }
}`;

// Cache: card info + race info, keyed by venue_raceNo
const cardCache = {};

async function getCardMap(venue, raceNo) {
  const key = `${venue}_${raceNo}`;
  if (cardCache[key]) return cardCache[key];

  try {
    const { raceMeetings } = await api.getRaceMeetings();
    const meeting = raceMeetings.find(m => m.venueCode === venue);
    if (meeting) {
      const race = meeting.races.find(r => Number(r.no) === raceNo);
      if (race) {
        // ── Build runner map ──────────────────────────────────
        const map = {};
        for (const r of (race.runners || [])) {
          const no = String(r.no);
          map[no] = {
            name:    r.name_ch    || r.name_en    || '',
            draw:    String(r.barrierDrawNumber || ''),
            jockey:  r.jockey?.name_ch  || r.jockey?.name_en  || '',
            trainer: r.trainer?.name_ch || r.trainer?.name_en || '',
          };
        }

        // ── Extract race info fields ──────────────────────────
        const raceInfo = extractRaceInfo(race);

        const result = { map, raceInfo };
        cardCache[key] = result;
        return result;
      }
    }
  } catch(e) {
    console.log('[WARN] getCardMap:', e.message.substring(0, 100));
  }
  return { map: {}, raceInfo: {} };
}

function extractRaceInfo(race) {
  if (!race) return {};
  try {
    // Different versions of hkjc-api may use slightly different field names
    // Try all known variants
    const raceTime  = race.postTime       || race.raceTime      || race.startTime    || '';
    const distance  = race.distance       || race.raceDistance  || '';
    const distStr   = distance ? (String(distance).includes('m') ? String(distance) : String(distance) + 'm') : '';
    const going     = race.going?.name_ch || race.going?.name_en || race.going        || race.trackState   || '';
    const course    = race.course?.name_ch|| race.course?.name_en|| race.courseName   || race.trackCode    || '';
    const track     = race.surface?.name_ch|| race.surface?.name_en
                   || (race.surfaceCode === 'AWT' ? '全天候跑道' : race.surfaceCode === 'TURF' ? '草地' : race.surfaceCode || '草地');
    const raceClass = race.raceClass?.name_ch || race.raceClass?.name_en || race.classInfo || race.raceClassName || '';
    const prize     = race.prize          || race.prizeMoney    || '';
    const prizeStr  = prize ? `$${Number(String(prize).replace(/[^0-9]/g,'')).toLocaleString()}` : '—';
    const raceName  = race.name_ch        || race.name_en       || race.raceName      || '';

    return {
      race_time:   String(raceTime).slice(0, 5),  // e.g. "12:45"
      distance:    distStr,                         // e.g. "1200m"
      track:       track,                           // e.g. "草地"
      course:      course,                          // e.g. '"B" 賽道(B)'
      race_class:  raceClass,                       // e.g. "新馬賽"
      going:       going,                           // e.g. "好地"
      prize:       prizeStr,                        // e.g. "$1,000,000"
      race_name:   raceName,                        // e.g. "啟德河谷盃"
    };
  } catch(e) {
    console.log('[WARN] extractRaceInfo:', e.message);
    return {};
  }
}

app.get('/odds', async (req, res) => {
  try {
    const { date, venue, raceno } = req.query;
    const raceNo = parseInt(raceno) || 1;
    console.log(`[INFO] ${venue} R${raceNo} ${date}`);

    const [oddsData, poolData, cardResult] = await Promise.all([
      gql.request(horseOddsQuery, { date, venueCode: venue, raceNo, oddsTypes: ['WIN', 'PLA'] }),
      gql.request(horsePoolQuery, { date, venueCode: venue, raceNo, oddsTypes: ['WIN'] }),
      getCardMap(venue, raceNo),
    ]);

    const cardMap  = cardResult.map      || {};
    const raceInfo = cardResult.raceInfo || {};

    let winPool = '';
    try {
      const wp = (poolData.raceMeetings?.[0]?.poolInvs || []).find(p => p.oddsType === 'WIN');
      winPool = wp ? String(wp.investment || '') : '';
    } catch(e) {}

    const winOddsMap = {};
    const plaOddsMap = {};
    for (const pool of (oddsData.raceMeetings?.[0]?.pmPools || [])) {
      for (const node of (pool.oddsNodes || [])) {
        const no = node.combString.replace(/^0+/, '');
        if (pool.oddsType === 'WIN') winOddsMap[no] = node.oddsValue;
        if (pool.oddsType === 'PLA') plaOddsMap[no] = node.oddsValue;
      }
    }

    if (Object.keys(winOddsMap).length === 0) {
      return res.json({ ok: false, error: `無賠率數據 ${venue} R${raceNo}` });
    }

    const allNos = [...new Set([...Object.keys(winOddsMap), ...Object.keys(plaOddsMap)])]
      .sort((a, b) => Number(a) - Number(b));

    const results = allNos.map(no => {
      const info = cardMap[no] || {};
      return {
        no,
        name:           info.name    || '',
        barrier:        info.draw    || '',
        jockey:         info.jockey  || '',
        trainer:        info.trainer || '',
        win:            winOddsMap[no] || 'SCR',
        place:          plaOddsMap[no] || '',
        win_investment: 0,
      };
    });

    // ── Return race info alongside results ───────────────────
    res.json({
      ok:        true,
      results,
      win_pool:  winPool,
      race_time: raceInfo.race_time  || '',
      distance:  raceInfo.distance   || '',
      track:     raceInfo.track      || '',
      course:    raceInfo.course     || '',
      race_class:raceInfo.race_class || '',
      going:     raceInfo.going      || '',
      prize:     raceInfo.prize      || '',
      race_name: raceInfo.race_name  || '',
    });

  } catch(e) {
    console.error('[ERROR]', e.message.substring(0, 300));
    res.json({ ok: false, error: e.message.substring(0, 300) });
  }
});

// ── Debug endpoint: dump raw race object to see all field names ──
app.get('/debug_race', async (req, res) => {
  try {
    const { venue, raceno } = req.query;
    const raceNo = parseInt(raceno) || 1;
    const { raceMeetings } = await api.getRaceMeetings();
    const meeting = raceMeetings.find(m => m.venueCode === (venue || 'ST'));
    if (!meeting) return res.json({ ok: false, error: 'No meeting found' });
    const race = meeting.races.find(r => Number(r.no) === raceNo);
    if (!race) return res.json({ ok: false, error: `Race ${raceNo} not found` });
    // Return the full raw race object (excluding runners array for brevity)
    const { runners, ...raceFields } = race;
    res.json({ ok: true, race: raceFields, runnerCount: runners?.length });
  } catch(e) {
    res.json({ ok: false, error: e.message });
  }
});

app.get('/meetings', async (req, res) => {
  try {
    const meetings = await api.getActiveMeetings();
    res.json({ ok: true, meetings });
  } catch(e) {
    res.json({ ok: false, error: e.message });
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`✅ HKJC bridge running on port ${PORT}`);
});
