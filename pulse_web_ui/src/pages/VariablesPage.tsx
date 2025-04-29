import React, { useState } from 'react';
import useFetchData from '../hooks/useApi';
import { Variables } from '../types';

/**
 * VariablesPage component to display and edit variables.
 * Fetches variables using the useFetchData hook and allows updating them.
 */
function VariablesPage() {
  const { data: variables, loading, error, refetch } = useFetchData<Variables>('/api/variables');
  const [editingVariable, setEditingVariable] = useState<string | null>(null);
  const [editedValue, setEditedValue] = useState<any>(null);
  const [updateStatus, setUpdateStatus] = useState<{ type: 'success' | 'error', message: string } | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);

  const handleEditClick = (name: string, value: any) => {
    setEditingVariable(name);
    setEditedValue(value);
    setUpdateStatus(null); // Clear previous status
  };

  const handleSaveClick = async (name: string) => {
    setIsUpdating(true);
    setUpdateStatus(null); // Clear previous status
    try {
      const response = await fetch(`/api/variables/${name}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ value: editedValue }),
      });

      const data = await response.json();

      if (response.ok) {
        setUpdateStatus({ type: 'success', message: data.message });
        setEditingVariable(null); // Exit editing mode
        setEditedValue(null);
        refetch(); // Refetch variables to show updated value
      } else {
        setUpdateStatus({ type: 'error', message: data.error || 'Failed to update variable.' });
      }
    } catch (err: any) {
      setUpdateStatus({ type: 'error', message: err.message || 'An error occurred during update.' });
    } finally {
      setIsUpdating(false);
    }
  };

  const handleCancelClick = () => {
    setEditingVariable(null);
    setEditedValue(null);
    setUpdateStatus(null); // Clear previous status
  };

  return (
    <div>
      <h1>Variables</h1>
      <div style={{ border: '1px solid black', padding: '20px', margin: '20px' }}>
        <h2>Variables Content</h2>
        {loading && <p>Loading variables...</p>}
        {error && <p>Error loading variables: {error.message}</p>}
        {updateStatus && (
          <p style={{ color: updateStatus.type === 'success' ? 'green' : 'red' }}>
            {updateStatus.message}
          </p>
        )}
        {variables && (
          <ul>
            {Object.entries(variables).map(([name, variable]) => (
              <li key={name}>
                <strong>{name}:</strong>{' '}
                {editingVariable === name ? (
                  <>
                    <input
                      type={variable.type === 'boolean' ? 'checkbox' : 'text'}
                      checked={variable.type === 'boolean' ? editedValue : undefined}
                      value={variable.type !== 'boolean' ? editedValue : ''}
                      onChange={(e) => setEditedValue(variable.type === 'boolean' ? e.target.checked : e.target.value)}
                      disabled={isUpdating}
                    />
                    <button onClick={() => handleSaveClick(name)} disabled={isUpdating}>Save</button>
                    <button onClick={handleCancelClick} disabled={isUpdating}>Cancel</button>
                  </>
                ) : (
                  <>
                    Value: {variable.type === 'boolean' ? String(variable.value) : variable.value}, Type: {variable.type}
                    <button onClick={() => handleEditClick(name, variable.value)} disabled={isUpdating}>Edit</button>
                  </>
                )}
              </li>
            ))}
          </ul>
        )}
        {!loading && !error && !variables && (
          <p>No variables data available.</p>
        )}
      </div>
    </div>
  );
}

export default VariablesPage;