import { ref, onMounted } from 'vue'

export interface RunItem {
  id: string
  label: string
  timestamp: string
  isCurrent: boolean
}

export interface FileItem {
  name: string
  size: number
  mtime: string
  type: 'csv' | 'markdown' | 'html' | 'other'
}

const runs = ref<RunItem[]>([])
const currentRunId = ref<string>('current')
const runSummary = ref<any>(null)
const runFiles = ref<FileItem[]>([])
const isLoading = ref<boolean>(false)
const error = ref<string | null>(null)

export function useRuns() {
  async function fetchRuns() {
    try {
      isLoading.value = true
      error.value = null
      const res = await fetch('/api/runs')
      if (!res.ok) throw new Error(`Failed to fetch runs: ${res.statusText}`)
      const data = await res.json()
      runs.value = data.runs || []
      if (!runs.value.some(r => r.id === currentRunId.value) && runs.value.length > 0) {
        currentRunId.value = runs.value[0].id
      }
    } catch (e: any) {
      error.value = e.message
    } finally {
      isLoading.value = false
    }
  }

  async function loadRunData(runId: string) {
    currentRunId.value = runId
    isLoading.value = true
    error.value = null
    try {
      const [summaryRes, filesRes] = await Promise.all([
        fetch(`/api/runs/${runId}/summary`),
        fetch(`/api/runs/${runId}/files`),
      ])

      if (summaryRes.ok) {
        runSummary.value = await summaryRes.json()
      }
      if (filesRes.ok) {
        const fileData = await filesRes.json()
        runFiles.value = fileData.files || []
      }
    } catch (e: any) {
      error.value = e.message
    } finally {
      isLoading.value = false
    }
  }

  async function selectRun(runId: string) {
    await loadRunData(runId)
  }

  return {
    runs,
    currentRunId,
    runSummary,
    runFiles,
    isLoading,
    error,
    fetchRuns,
    loadRunData,
    selectRun,
  }
}
