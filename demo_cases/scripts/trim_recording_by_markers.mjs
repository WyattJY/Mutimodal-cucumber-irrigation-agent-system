import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const demoRoot = path.resolve(__dirname, '..')
const recordingsDir = path.join(demoRoot, 'recordings')

const inputMp4 = process.argv[2] || path.join(recordingsDir, 'agriagent-ui-demo.raw.mp4')
const outputMp4 = process.argv[3] || path.join(recordingsDir, 'agriagent-ui-demo.mp4')
const markersPath = process.argv[4] || path.join(recordingsDir, 'recording-markers.json')
const ffmpegBin = process.env.FFMPEG_BIN || 'ffmpeg'

if (!existsSync(inputMp4)) {
  throw new Error(`Input MP4 not found: ${inputMp4}`)
}
if (!existsSync(markersPath)) {
  throw new Error(`Recording markers not found: ${markersPath}`)
}

const markers = JSON.parse(await readFile(markersPath, 'utf-8'))
const markerAt = (name) => markers.find((item) => item.name === name)?.seconds

function computeCut({ start, end, seconds, lead, tail }) {
  const startAt = markerAt(start)
  const endAt = markerAt(end)
  if (!Number.isFinite(startAt) || !Number.isFinite(endAt) || endAt <= startAt) return null

  const available = endAt - startAt - lead - tail
  if (available <= 0.5) return null

  const cutLength = Math.min(seconds, Math.max(0, available - 0.1))
  const cutStart = startAt + lead
  const cutEnd = cutStart + cutLength
  if (cutEnd >= endAt - tail) return null

  return {
    label: `${start}->${end}`,
    start: Number(cutStart.toFixed(3)),
    end: Number(cutEnd.toFixed(3)),
    seconds: Number(cutLength.toFixed(3)),
  }
}

const cuts = [
  computeCut({
    start: 'vision_upload_start',
    end: 'vision_result_ready',
    seconds: 4,
    lead: 1,
    tail: 0.5,
  }),
  computeCut({
    start: 'predict_submit',
    end: 'predict_result_ready',
    seconds: 4,
    lead: 1,
    tail: 0.5,
  }),
  process.env.DEMO_TRIM_PDF_UPLOAD === '1'
    ? computeCut({
      start: 'pdf_upload_start',
      end: 'pdf_indexed_ready',
      seconds: 8,
      lead: 2,
      tail: 0.5,
    })
    : null,
].filter(Boolean)

const selectExpr = cuts.length
  ? `select='not(${cuts.map((cut) => `between(t,${cut.start},${cut.end})`).join('+')})',setpts=N/FRAME_RATE/TB`
  : 'setpts=N/FRAME_RATE/TB'

console.log('Applied cuts:')
for (const cut of cuts) {
  console.log(`- ${cut.label}: ${cut.start}s -> ${cut.end}s (${cut.seconds}s)`)
}
if (!cuts.length) {
  console.log('- none; no long wait interval was detected')
}

await new Promise((resolve, reject) => {
  const child = spawn(ffmpegBin, [
    '-y',
    '-i',
    inputMp4,
    '-vf',
    selectExpr,
    '-an',
    '-movflags',
    '+faststart',
    outputMp4,
  ], { stdio: 'inherit' })

  child.on('error', reject)
  child.on('exit', (code) => {
    if (code === 0) resolve()
    else reject(new Error(`ffmpeg exited with code ${code}`))
  })
})

console.log(`Trimmed MP4 written to ${outputMp4}`)
