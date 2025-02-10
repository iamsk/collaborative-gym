import { initEnvironment } from '@/lib/api';

export async function handleStartSession(
  formData: FormData,
  userId: string
) {
  const task = formData.get('task') as string;
  const inputs: any = {};
  const files = new FormData();

  if (task === 'lit_survey') {
    inputs.query = formData.get('query');
  } else if (task === 'tabular_analysis') {
    inputs.query = formData.get('query');
    const tables = formData.getAll('tables');
    tables.forEach((table, i) => {
      files.append(`table${i}`, table);
    });
  } else if (task === 'travel_planning') {
    inputs.query = formData.get('query');
  }

  const info = await initEnvironment(userId, task, inputs, files);
  const sessionId = info?.session_id;

  if (info && sessionId) {
    return { sessionId, task };
  } else {
    throw new Error('Failed to start session');
  }
}
