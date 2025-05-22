export interface ExtractedData {
  project_name: string;
  description: string;
  key_features: string[];
  deadline?: string;
  budget?: string;
  client_requirements?: string;
  priority: 'low' | 'medium' | 'high';
}

export interface ProposalVersion {
  content: string;
  pdf_path?: string;
  version: number;
  created_at: string;
  modified_by?: string;
}

export interface ApprovalHistory {
  user_id: string;
  decision: 'approved' | 'rejected' | 'requested_changes';
  timestamp: string;
  comments?: string;
}

export interface Proposal {
  _id: string;
  email_id: string;
  extracted_data: ExtractedData;
  proposal_versions: ProposalVersion[];
  current_status: 'draft' | 'under_review' | 'approved' | 'rejected' | 'sent';
  approval_history: ApprovalHistory[];
  metadata: Record<string, any>;
  timestamps: Record<string, string>;
}

export interface ProposalListParams {
  status?: string;
  skip?: number;
  limit?: number;
}