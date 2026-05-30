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

const cardCache = {};
setInterval(() => {
  Object.keys(cardCache).forEach(k => delete cardCache[k]);
  console.log('[INFO] Card cache cleared');
}, 10 * 60 * 1000);

async function getCardAndRaceInfo(venue, raceNo) {
  const key = `${venue}_${raceNo}`;
  if (cardCache[key]) return cardCache[key];

  try {
    const { raceMeetings } = await api.getRaceMeetings({ venueCode: venue });
    const meeting = (raceMeetings || []).find(m => m.venueCode === venue);
    if (!meeting) {
      console.log(`[WARN] No meeting found for venue ${venue}`);
      return { map: {}, raceInfo: {} };
    }

    const race = (meeting.races || []).find(r => Number(r.no) === raceNo);
    if (!race) {
      console.log(`[WARN] Race ${raceNo} not found`);
      return { map: {}, raceInfo: {} };
    }

    // Log full race object so we can see every real field name
    const { runners, ...raceFields } = race;
    console.log('[DEBUG] FULL RACE OBJECT:', JSON.stringify(raceFields, null, 2));

    const map = {};
    for (const r of (runners || [])) {
      const no = String(r.no);
      map[no] = {
        name:    r.name_ch    || r.name_en    || '',
        draw:    String(r.barrierDrawNumber || r.barrier || r.draw || ''),
        jockey:  r.jockey?.name_ch  || r.jockey?.name_en  || r.jockey  || '',
        trainer: r.trainer?.name_ch || r.trainer?.name_en || r.trainer || '',
      };
    }

    const raceInfo = buildRaceInfo(race);
    const result = { map, raceInfo };
    cardCache[key] = result;
    return result;

  } catch(e) {
    console.log('[WARN] getCardAndRaceInfo:', e.message.substring(0, 200));
    return { map: {}, raceInfo: {} };
  }
}

// Helper: extract string from field that may be string, number, or {name_ch, name_en}
function str(v) {
  if (!v && v !== 0) return '';
  if (typeof v === 'object') return v.name_ch || v.name_en || v.ch || v.en || JSON.stringify(v);
  return String(v);
}

function buildRaceInfo(r) {
  if (!r) return {};

  // ── Time: ISO format "2026-05-31T12:45:00+08:00" → "12:45" ──
  const rawTime = r.postTime || r.raceTime || r.startTime || r.time || r.raceStartTime || '';
  let raceTime = '';
  if (rawTime) {
    const m = String(rawTime).match(/T(\d{2}:\d{2})/);
    raceTime = m ? m[1] : String(rawTime).slice(0, 5);
  }

  // ── Distance: number like 1200 or string "1200m" ─────────
  const rawDist = r.distance || r.raceDistance || r.dist || '';
  const distance = rawDist ? String(rawDist).replace(/(\d+)\s*[mM]?$/, '$1') + 'm' : '';

  // ── Track surface ─────────────────────────────────────────
  // Try every known field name
  const surfRaw = r.surface      || r.surfaceCode  || r.trackSurface
               || r.raceSurface  || r.trackType    || r.turf
               || r.groundType   || '';
  let track = str(surfRaw);
  const su = track.toUpperCase();
  if (su === 'TURF' || su === 'T')         track = '草地';
  else if (su === 'AWT' || su === 'A')     track = '全天候跑道';
  else if (su === 'DIRT' || su === 'D')    track = '泥地';

  // ── Course / Rail ─────────────────────────────────────────
  const courseRaw = r.course       || r.courseName   || r.courseCode
                 || r.trackCourse  || r.railPosition  || r.track
                 || r.trackName    || r.courseInfo    || '';
  const course = str(courseRaw);

  // ── Class ─────────────────────────────────────────────────
  const classRaw = r.raceClass     || r.classInfo    || r.class
                || r.raceCategory  || r.className    || r.gradeInfo
                || r.grade         || r.raceGrade    || r.category || '';
  const raceClass = str(classRaw);

  // ── Going ─────────────────────────────────────────────────
  const goingRaw = r.going         || r.trackCondition || r.trackState
                || r.groundCondition || r.goingCode   || r.condition
                || r.trackGoing    || r.goingDesc     || '';
  const going = str(goingRaw);

  // ── Prize ─────────────────────────────────────────────────
  const prizeRaw = r.prize || r.prizeMoney || r.prizeMoneyHKD
                || r.totalPrize  || r.prizePool || r.purse || '';
  const prizeNum = Number(String(prizeRaw).replace(/[^0-9]/g, ''));
  const prize = prizeNum > 0 ? '$' + prizeNum.toLocaleString() : '—';

  // ── Race name ─────────────────────────────────────────────
  const raceName = r.name_ch || r.name_en || r.raceName
                || r.raceNameCh || r.raceNameEn || r.title || '';

  console.log('[DEBUG] buildRaceInfo result:', { raceTime, distance, track, course, raceClass, going, prize, raceName });

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

// ── /debug_race: paste output here so we can fix field names instantly ──
app.get('/debug_race', async (req, res) => {
  try {
    const venue  = req.query.venue  || 'ST';
    const raceNo = parseInt(req.query.raceno) || 1;
    const { raceMeetings } = await api.getRaceMeetings({ venueCode: venue });
    const meeting = (raceMeetings || []).find(m => m.venueCode === venue);
    if (!meeting) return res.json({ ok: false, error: 'No meeting', allVenues: raceMeetings.map(m=>m.venueCode) });
    const race = (meeting.races || []).find(r => Number(r.no) === raceNo);
    if (!race) return res.json({ ok: false, error: `Race ${raceNo} not found`, available: meeting.races.map(r=>r.no) });
    const { runners, ...raceFields } = race;
    const sampleRunner = runners?.[0] ? { ...runners[0] } : {};
    res.json({ ok: true, raceFields, runnerSample: sampleRunner });
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
