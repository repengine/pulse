import { useState, useEffect, useCallback } from 'react';
import { ApiError } from '../types';

/**
 * Custom hook for fetching data from an API endpoint with manual refetching.
 * @param url The API endpoint URL to fetch data from.
 * @returns An object containing the data, loading state, error state, and a refetch function.
 */
function useApi<T>(initialUrl: string = '') {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const get = useCallback(async (url: string = initialUrl) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(url);
      if (!response.ok) {
        const errorBody = await response.json();
        throw new Error(errorBody.message || `HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      setData(result);
      return result; // Return data on success
    } catch (err: any) {
      setError({ message: err.message, status: err.status });
      throw err; // Re-throw error on failure
    } finally {
      setLoading(false);
    }
  }, [initialUrl]);

  const post = useCallback(async (url: string, body: any) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        const errorBody = await response.json();
        throw new Error(errorBody.message || `HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      setData(result);
      return result; // Return data on success
    } catch (err: any) {
      setError({ message: err.message, status: err.status });
      throw err; // Re-throw error on failure
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, get, post, refetch: get };
}

export default useApi;