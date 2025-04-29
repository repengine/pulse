import { useState, useEffect, useCallback } from 'react';
import { ApiError } from '../types';

/**
 * Custom hook for fetching data from an API endpoint with manual refetching.
 * @param url The API endpoint URL to fetch data from.
 * @returns An object containing the data, loading state, error state, and a refetch function.
 */
function useFetchData<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetchData = useCallback(async () => {
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
    } catch (err: any) {
      setError({ message: err.message, status: err.status });
    } finally {
      setLoading(false);
    }
  }, [url]); // Re-create fetchData if the URL changes

  useEffect(() => {
    fetchData();
  }, [fetchData]); // Re-run effect if fetchData changes (due to URL change)

  return { data, loading, error, refetch: fetchData };
}

export default useFetchData;