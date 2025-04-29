// Basic interfaces for data structures fetched from the backend.
// These can be refined later based on the actual data shapes.

export interface DataOverview {
  [key: string]: any;
}

export interface Forecasts {
  [key: string]: any;
}

export interface LogEntry {
  timestamp: string;
  severity: string;
  message: string;
}

export interface Logs extends Array<LogEntry> {}

export interface Variables {
  [key: string]: any;
}

export interface ApiError {
  message: string;
  status?: number;
}