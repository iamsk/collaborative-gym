import axios from 'axios';

export const API_URL = process.env.NEXT_PUBLIC_API_URL;

export const initEnvironment = async (
  userId: string,
  envClass: string,
  envArgs: any,
  files: FormData
) => {
  console.log('Initializing environment. User ID:', userId);
  console.log('Environment Class:', envClass);
  console.log('Environment Args:', envArgs);
  const fileFormData = new FormData();
  fileFormData.append('user_id', userId);
  fileFormData.append('env_class', envClass);
  fileFormData.append('env_args', JSON.stringify(envArgs));
  for (const [, value] of files.entries()) {
    fileFormData.append('files', value);
  }
  try {
    const response = await axios.post(`${API_URL}/init_env`, fileFormData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  } catch (error) {
    console.error(error);
    return null;
  }
};

export const postAction = async (
  envId: string,
  userId: string,
  actionString: string
) => {
  console.log('Posting action:', actionString);
  try {
    const response = await axios.post(
      `${API_URL}/post_action/${envId}/${userId}`,
      { action: actionString }
    );
    console.log('Action Response:', response);
    return response.data;
  } catch (error) {
    console.error('Error posting action:', error);
    return null;
  }
};

export const getTables = async (envId: string) => {
  console.log('Getting tables for environment:', envId);
  try {
    const response = await axios.get(`${API_URL}/tables/${envId}`);
    return response.data;
  } catch (error) {
    console.error('Error getting tables:', error);
    return null;
  }
};

export const getResult = async (envId: string) => {
  console.log('Getting result for environment:', envId);
  try {
    const response = await axios.get(`${API_URL}/result/${envId}`);
    return response.data;
  } catch (error) {
    console.error('Error getting result:', error);
    return null;
  }
};
