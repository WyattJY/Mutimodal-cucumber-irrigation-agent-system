export interface UploadProgressSnapshot {
  loaded: number
  total?: number
  percent: number
  etaSeconds?: number
}

export type UploadProgressHandler = (progress: UploadProgressSnapshot) => void

export interface ChatImageAttachment {
  attachment_id: string
  original_filename: string
  stored_filename: string
  stored_path: string
  metadata_path?: string
  public_url: string
  mime_type: string
  size_bytes: number
  uploaded_at?: string
}
