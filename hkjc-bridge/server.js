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

// Cache card + race info, keyed by venue_raceNo
// Clear cache every 10 minutes so fresh data is picked up
const cardCache = {};
setInterval(() => {
  Object.keys(cardCache).forEach(k => delete cardCache[k]);
  console.log('[INFO] Card cache cleared');
}, 10 * 60 * 1000);

async function getCardAndRaceInfo(venue, raceNo) {
  const key = `${venue}_${raceNo}`;
  if (cardCache[key]) return cardCache[key];

  try {
    // Use getRaceMeetings with venue + date filters for accuracy
    const { raceMeetings } = await api.getRaceMeetings({ venueCode: venue });
    const meeting = (raceMeetings || []).find(m => m.venueCode === venue);

    if (!meeting) {
      console.log(`[WARN] No meeting found for venue ${venue}`);
      return { map: {}, raceInfo: {} };
    }

    const race = (meeting.races || []).find(r => Number(r.no) === raceNo);
    if (!race) {
      console.log(`[WARN] Race ${raceNo} not found in meeting`);
      return { map: {}, raceInfo: {} };
    }

    // Log raw race keys so we can debug field names
    console.log('[DEBUG] race keys:', Object.keys(race).join(', '));
    console.log('[DEBUG] race sample:', JSON.stringify(race, null, 2).substring(0, 800));

    // Build runner map
    const map = {};
    for (const r of (race.runners || [])) {
      const no = String(r.no);
      map[no] = {
        name:    r.name_ch    || r.name_en    || '',
        draw:    String(r.barrierDrawNumber || r.barrier || r.draw || ''),
        jockey:  r.jockey?.name_ch  || r.jockey?.name_en  || r.jockey  || '',
        trainer: r.trainer?.name_ch || r.trainer?.name_en || r.trainer || '',
      };
    }

    // Extract race info — log shows exact keys available
    const raceInfo = buildRaceInfo(race);
    console.log('[DEBUG] raceInfo built:', raceInfo);

    const result = { map, raceInfo };
    cardCache[key] = result;
    return result;

  } catch(e) {
    console.log('[WARN] getCardAndRaceInfo:', e.message.substring(0, 200));
    return { map: {}, raceInfo: {} };
  }
}

function buildRaceInfo(r) {
  if (!r) return {};

  // ── Time ────────────────────────────────────────────────
  const rawTime = r.postTime || r.raceTime || r.startTime
               || r.time     || r.raceStartTime || '';
  const raceTime = String(rawTime).replace(/^(\d{2}:\d{2}).*/, '$1'); // keep HH:MM

  // ── Distance ────────────────────────────────────────────
  const rawDist  = r.distance || r.raceDistance || r.dist || '';
  const distance = rawDist
    ? (String(rawDist).match(/\d+m?/i)
        ? String(rawDist).replace(/(\d+)([mM]?)/, '$1m')
        : String(rawDist) + 'm')
    : '';

  // ── Track surface (草地 / 全天候) ─────────────────────
  const surfCode = r.surfaceCode || r.trackType || r.surface || '';
  let track = '';
  if (typeof surfCode === 'object') {
    track = surfCode.name_ch || surfCode.name_en || '';
  } else {
    const s = String(surfCode).toUpperCase();
    if (s === 'TURF' || s === 'T')   track = '草地';
    else if (s === 'AWT' || s === 'A') track = '全天候跑道';
    else track = surfCode || '';
  }

  // ── Course / Rail ────────────────────────────────────────
  const rawCourse = r.course || r.courseName || r.track
                  || r.railPosition || r.courseCode || '';
  const course = typeof rawCourse === 'object'
    ? (rawCourse.name_ch || rawCourse.name_en || '')
    : String(rawCourse);

  // ── Class ────────────────────────────────────────────────
  const rawClass = r.raceClass || r.classInfo || r.class
                 || r.raceCategory || r.className || '';
  const raceClass = typeof rawClass === 'object'
    ? (rawClass.name_ch || rawClass.name_en || '')
    : String(rawClass);

  // ── Going ────────────────────────────────────────────────
  const rawGoing = r.going || r.trackCondition || r.trackState
                 || r.groundCondition || '';
  const going = typeof rawGoing === 'object'
    ? (rawGoing.name_ch || rawGoing.name_en || '')
    : String(rawGoing);

  // ── Prize ────────────────────────────────────────────────
  const rawPrize = r.prize || r.prizeMoney || r.prizeMoneyHKD || '';
  const prize = rawPrize
    ? '$' + Number(String(rawPrize).replace(/[^0-9]/g, '')).toLocaleString()
    : '—';

  // ── Race name ────────────────────────────────────────────
  const raceName = r.name_ch || r.name_en || r.raceName || r.raceNameEn || '';

  return { race_time: raceTime, distance, track, course, race_class: raceClass, going, prize, race_name: raceName };
}

app.get('/odds', async (req, res) => {
  try {
    const { date, venue, raceno } = req.query;
    const raceNo = parseInt(raceno) || 1;
    console.log(`[INFO] /odds ${venue} R${raceNo} ${date}`);

    const [oddsData, poolData, cardResult] = await Promise.all([
      gql.request(horseOddsQuery, { date, venueCode: venue, raceNo, oddsTypes: ['WIN', 'PLA'] }),
      gql.request(horsePoolQuery, { date, venueCode: venue, raceNo, oddsTypes: ['WIN'] }),
      getCardAndRaceInfo(venue, raceNo),
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

    res.json({
      ok:         true,
      results,
      win_pool:   winPool,
      race_time:  raceInfo.race_time  || '',
      distance:   raceInfo.distance   || '',
      track:      raceInfo.track      || '',
      course:     raceInfo.course     || '',
      race_class: raceInfo.race_class || '',
      going:      raceInfo.going      || '',
      prize:      raceInfo.prize      || '',
      race_name:  raceInfo.race_name  || '',
    });

  } catch(e) {
    console.error('[ERROR]', e.message.substring(0, 300));
    res.json({ ok: false, error: e.message.substring(0, 300) });
  }
});

// ── Debug: dump raw race object to find exact field names ──────────
app.get('/debug_race', async (req, res) => {
  try {
    const venue  = req.query.venue  || 'ST';
    const raceNo = parseInt(req.query.raceno) || 1;
    const { raceMeetings } = await api.getRaceMeetings({ venueCode: venue });
    const meeting = (raceMeetings || []).find(m => m.venueCode === venue);
    if (!meeting) return res.json({ ok: false, error: 'No meeting' });
    const race = (meeting.races || []).find(r => Number(r.no) === raceNo);
    if (!race) return res.json({ ok: false, error: `Race ${raceNo} not found` });
    const { runners, ...raceFields } = race;
    // Also show one runner's keys
    const sampleRunner = runners?.[0] || {};
    res.json({ ok: true, raceFields, runnerKeys: Object.keys(sampleRunner), runnerSample: sampleRunner });
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
