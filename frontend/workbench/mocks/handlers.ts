import { API_URL } from '@/lib/api';
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.post(`${API_URL}/init_env`, ({ request }) => {
    console.log('Mock API: Initializing Environment');
    return HttpResponse.json({
      message: 'Environment Initialized',
      session_id: '1234',
    });
  }),
];
