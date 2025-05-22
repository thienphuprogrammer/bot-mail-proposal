import { ProposalListParams } from '../types/proposal';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

export async function listProposals(params: ProposalListParams) {
  const queryParams = new URLSearchParams();
  if (params.status) queryParams.append('status', params.status);
  if (params.skip !== undefined) queryParams.append('skip', params.skip.toString());
  if (params.limit !== undefined) queryParams.append('limit', params.limit.toString());

  const response = await fetch(`${API_BASE_URL}/proposals/?${queryParams}`);
  if (!response.ok) throw new Error('Failed to fetch proposals');
  return response.json();
}

export async function getProposal(proposalId: string) {
  const response = await fetch(`${API_BASE_URL}/proposals/${proposalId}`);
  if (!response.ok) throw new Error('Failed to fetch proposal');
  return response.json();
}

export async function generateProposal(proposalId: string) {
  const response = await fetch(`${API_BASE_URL}/proposals/${proposalId}/generate`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to generate proposal');
  return response.json();
}

export async function generatePdf(proposalId: string) {
  const response = await fetch(`${API_BASE_URL}/proposals/${proposalId}/generate-pdf`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to generate PDF');
  return response.json();
}

export async function sendProposal(proposalId: string, options: {
  custom_subject?: string;
  custom_message?: string;
  custom_recipient?: string;
  cc_recipients?: string[];
  bcc_recipients?: string[];
}) {
  const response = await fetch(`${API_BASE_URL}/proposals/${proposalId}/send`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(options),
  });
  if (!response.ok) throw new Error('Failed to send proposal');
  return response.json();
}

export async function approveProposal(proposalId: string, notes?: string) {
  const queryParams = new URLSearchParams();
  if (notes) queryParams.append('approval_notes', notes);

  const response = await fetch(`${API_BASE_URL}/proposals/${proposalId}/approve?${queryParams}`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to approve proposal');
  return response.json();
}