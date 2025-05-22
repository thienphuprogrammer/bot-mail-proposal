export interface Email {
  email_id: string;
  sender: string;
  subject: string;
  body: string;
  attachments: string[];
  received_at: string;
  processing_status: string;
  error_log?: string;
  is_encrypted: boolean;
  _id: string;
}

export interface EmailStats {
  total: number;
  processed: number;
  pending: number;
  failed: number;
}

export interface EmailListParams {
  show_processed?: boolean;
  show_unprocessed?: boolean;
  skip?: number;
  limit?: number;
}