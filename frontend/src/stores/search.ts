import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import * as searchApi from '@/api/search'

export interface Citation {
  paragraph_index: number
  paragraph_title: string
  query: string
  url: string | null
  title: string | null
  content: string | null
  score: number | null
  search_count: number
  reflection_count: number
}

export interface EngineState {
  status: 'idle' | 'running' | 'done' | 'error'
  progressPct: number
  message: string
  paragraphCurrent: number
  paragraphTotal: number
  finalReport: string
  citations: Citation[]
  error: string
}

function emptyEngineState(): EngineState {
  return {
    status: 'idle',
    progressPct: 0,
    message: '',
    paragraphCurrent: 0,
    paragraphTotal: 0,
    finalReport: '',
    citations: [],
    error: '',
  }
}

export const useSearchStore = defineStore('search', () => {
  const query = ref('')
  const searching = ref(false)
  const lastResult = ref<any>(null)

  // Store active EventSource for cleanup
  let activeEventSource: EventSource | null = null

  const engines = reactive<Record<string, EngineState>>({
    insight: emptyEngineState(),
    media: emptyEngineState(),
    query: emptyEngineState(),
  })

  function resetEngine(engine: string) {
    Object.assign(engines[engine], emptyEngineState())
  }

  function cancelStream() {
    if (activeEventSource) {
      activeEventSource.close()
      activeEventSource = null
    }
    searching.value = false
  }

  function handleEngineProgress(data: any) {
    const engine = data.engine
    if (!engines[engine]) return
    engines[engine].status = 'running'
    engines[engine].progressPct = data.progress_pct ?? 0
    engines[engine].message = data.message ?? ''
    engines[engine].paragraphCurrent = data.paragraph_current ?? 0
    engines[engine].paragraphTotal = data.paragraph_total ?? 0
  }

  function handleEngineResult(data: any) {
    const engine = data.engine
    if (!engines[engine]) return
    engines[engine].status = 'done'
    engines[engine].progressPct = 100
    engines[engine].finalReport = data.final_report ?? ''
    engines[engine].citations = data.citations ?? []
    engines[engine].message = '研究完成'
  }

  function handleEngineError(data: any) {
    const engine = data.engine
    if (!engines[engine]) return
    engines[engine].status = 'error'
    engines[engine].error = data.error ?? '未知错误'
    engines[engine].message = data.error ?? '研究出错'
  }

  async function fetchLatestResults() {
    const res = await searchApi.fetchLatestResults()
    const results = res.data?.results || {}
    Object.entries(results).forEach(([engine, data]: [string, any]) => {
      if (engines[engine] && data?.final_report) {
        handleEngineResult(data)
      }
    })
    return res.data
  }

  async function performSearch(q: string) {
    query.value = q
    searching.value = true
    // Reset all engines for new search
    resetEngine('insight')
    resetEngine('media')
    resetEngine('query')
    try {
      const res = await searchApi.search(q)
      lastResult.value = res.data
      return res.data
    } finally {
      searching.value = false
    }
  }

  async function performSearchStream(q: string) {
    // Cancel any existing stream
    cancelStream()

    query.value = q
    searching.value = true
    // Reset all engines for new search
    resetEngine('insight')
    resetEngine('media')
    resetEngine('query')

    try {
      activeEventSource = new EventSource(`/api/search/stream?query=${encodeURIComponent(q)}`)

      activeEventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          if (data.type === 'progress') {
            handleEngineProgress(data)
          } else if (data.type === 'result') {
            // Update engine state with result
            const engine = data.engine
            if (engines[engine]) {
              engines[engine].status = 'done'
              engines[engine].progressPct = 100
              engines[engine].finalReport = data.report || ''
              engines[engine].citations = data.citations || []
              engines[engine].message = '研究完成'
            }
          } else if (data.type === 'complete') {
            searching.value = false
            activeEventSource?.close()
            activeEventSource = null
          } else if (data.type === 'timeout') {
            searching.value = false
            activeEventSource?.close()
            activeEventSource = null
          }
        } catch (e) {
          console.error('Error parsing SSE data:', e)
        }
      }

      activeEventSource.onerror = () => {
        searching.value = false
        // Set error state for running engines
        Object.keys(engines).forEach(key => {
          if (engines[key].status === 'running') {
            engines[key].status = 'error'
            engines[key].error = '连接中断'
            engines[key].message = '连接中断'
          }
        })
        activeEventSource?.close()
        activeEventSource = null
      }

      return { success: true }
    } catch (error) {
      searching.value = false
      activeEventSource = null
      return { success: false, error }
    }
  }

  return {
    query, searching, lastResult, engines,
    resetEngine, cancelStream, handleEngineProgress, handleEngineResult, handleEngineError,
    performSearch, performSearchStream, fetchLatestResults,
  }
})
