import { EmailListParams } from '../types/email';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;


export async function listEmails(params: EmailListParams) {
  const queryParams = new URLSearchParams();
  if (params.show_processed !== undefined) queryParams.append('show_processed', params.show_processed.toString());
  if (params.show_unprocessed !== undefined) queryParams.append('show_unprocessed', params.show_unprocessed.toString());
  if (params.skip !== undefined) queryParams.append('skip', params.skip.toString());
  if (params.limit !== undefined) queryParams.append('limit', params.limit.toString());

  const response = await fetch(`${API_BASE_URL}/emails/?${queryParams}`);
  if (!response.ok) throw new Error('Failed to fetch emails');
  return response.json();
}

export async function getEmailStats() {
  const response = await fetch(`${API_BASE_URL}/emails/stats/summary`);
  if (!response.ok) throw new Error('Failed to fetch email stats');
  return response.json();
}

export async function syncEmails(params?: {
  query?: string;
  max_results?: number;
  folder?: string;
  include_spam_trash?: boolean;
  only_recent?: boolean;
}) {
  const queryParams = new URLSearchParams();
  if (params?.query) queryParams.append('query', params.query);
  if (params?.max_results) queryParams.append('max_results', params.max_results.toString());
  if (params?.folder) queryParams.append('folder', params.folder);
  if (params?.include_spam_trash !== undefined) queryParams.append('include_spam_trash', params.include_spam_trash.toString());
  if (params?.only_recent !== undefined) queryParams.append('only_recent', params.only_recent.toString());

  const response = await fetch(`${API_BASE_URL}/emails/sync?${queryParams}`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to sync emails');
  return response.json();
}

export async function processEmail(emailId: string) {
  const response = await fetch(`${API_BASE_URL}/emails/${emailId}/process`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to process email');
  return response.json();
}