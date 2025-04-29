# Pulse Intelligence System UI - Conceptual Design Plan (Revision 1)

This document outlines the conceptual design for the Pulse Intelligence System's user interface, intended primarily for researchers interacting with the system.

**1. Overall Structure & Navigation:**

*   **Layout:** A modern web application layout featuring a persistent left-hand sidebar for primary navigation and a main content area that updates based on the selected section.
*   **Navigation Model:** The sidebar will contain links to the main functional areas:
    *   Dashboard (System Overview)
    *   Retrodiction
    *   Forecasting
    *   Memory Explorer
    *   Autopilot Control
    *   Settings/Configuration
*   **Header:** A minimal header could display the Pulse system name/logo and perhaps global status indicators or user information if needed in the future.

**2. Main UI Components:**

*   **A. Dashboard (System Overview):**
    *   **Purpose:** Provide a high-level, at-a-glance view of Pulse's current state.
    *   **Key Elements:**
        *   System Status Indicator: Clear visual cue (e.g., green/yellow/red icon/text).
        *   Active Processes: Indication of running Retrodiction, Forecasting, or Autopilot tasks.
        *   Resource Usage: Basic metrics (optional).
        *   Recent Activity Log: Feed of latest significant events.
        *   Recursive Learning Status: Display On/Off state.

*   **B. Retrodiction View:**
    *   **Purpose:** Allow researchers to explore and analyze the results of past retrodiction runs.
    *   **Key Elements:**
        *   Run Selector: Select specific retrodiction runs.
        *   Results Display: Summary Table (metrics), Detailed Insights (text), Visualizations (charts), Data Table (raw/processed data).
        *   Comparison Feature (Optional): View two runs side-by-side.

*   **C. Forecasting View:**
    *   **Purpose:** Enable researchers to view and assess generated forecasts.
    *   **Key Elements:**
        *   Forecast Selector: Select specific forecast sets.
        *   Forecast Display: Primary Forecast Chart (with confidence intervals), Metrics Table (probabilistic metrics), Scenario Analysis (Optional).
        *   Data Table: Access to underlying forecast data.

*   **D. Memory Explorer:**
    *   **Purpose:** Allow researchers to browse, search, and inspect internal knowledge structures (rules, concepts, data points) within Pulse's memory.
    *   **Key Elements:**
        *   Search/Filter Bar: Search or filter memory items.
        *   Browsing Pane: Navigate memory structure (list, hierarchy).
        *   Detail View: Display selected item's content.
        *   Metadata Display: Show source, timestamps, scores, etc.
        *   Relationship Visualization (Optional/Advanced): Visualize links between items.

*   **E. Autopilot Control View:**
    *   **Purpose:** Provide researchers with controls to manage and configure Autopilot runs.
    *   **Key Elements:**
        *   Status Display: Current state (running, idle, stopped) and active configuration.
        *   Run Controls: Buttons for "Start New Run," "Stop Current Run."
        *   Configuration Panel: Define Goals, Constraints, (Optional) Parameters.
        *   Run History: Table of past runs, configurations, status, links to results.

*   **F. Settings/Configuration View:**
    *   **Purpose:** Central location for system-wide settings.
    *   **Key Elements:**
        *   Recursive Learning Switch: Clear toggle with explanation.
        *   (Future) Other Settings: API keys, notifications, data sources, etc.

**3. Interaction & Data Flow (High-Level):**

*   The UI (Client/Frontend) communicates with a backend API via HTTP requests.
*   The backend API interacts with the core Pulse systems (Retrodiction Engine, Forecasting Engine, Autopilot Controller, Memory/Knowledge Manager, System State Manager, Recursive Learning Module).
*   User actions trigger API calls to fetch data or send commands.
*   The Dashboard may use polling or WebSockets for real-time updates.

**4. High-Level Component Diagram (Mermaid):**

```mermaid
graph TD
    subgraph Pulse UI (Web Application)
        A[Sidebar Navigation] --> B(Dashboard View);
        A --> C(Retrodiction View);
        A --> D(Forecasting View);
        A --> ME(Memory Explorer View);
        A --> E(Autopilot Control View);
        A --> F(Settings View);

        B -- Displays --> G{System Status};
        B -- Displays --> H{Active Processes};
        B -- Displays --> I{Recent Activity};
        B -- Displays --> J(Recursive Learning Status);

        C -- Selects Run --> K{Retrodiction Data};
        C -- Displays --> L[Results Table/Charts];
        C -- Displays --> M[Insights Text];

        D -- Selects Forecast --> N{Forecast Data};
        D -- Displays --> O[Forecast Chart];
        D -- Displays --> P[Metrics Table];

        ME -- Browses/Searches --> MEM_Data{Memory/Knowledge Data};
        ME -- Displays --> MEM_Details[Memory Item Details];

        E -- Controls --> Q{Autopilot State};
        E -- Configures --> R[Goals & Constraints];
        E -- Displays --> S[Run History];

        F -- Controls --> T(Recursive Learning Switch);
    end

    subgraph Pulse Backend API
        U[API Endpoints]
    end

    subgraph Core Pulse System
        V[Retrodiction Engine]
        W[Forecasting Engine]
        X[Autopilot Controller]
        Y[System State Manager]
        Z[Recursive Learning Module]
        MEM_MGR[Memory/Knowledge Manager]
    end

    Pulse_UI -- HTTP Requests --> U;
    U -- Interacts --> V;
    U -- Interacts --> W;
    U -- Interacts --> X;
    U -- Interacts --> Y;
    U -- Interacts --> Z;
    U -- Interacts --> MEM_MGR;

    Y --> G; Y --> H; Y --> I;
    Z --> J; Z --> T;
    V --> K;
    W --> N;
    MEM_MGR --> MEM_Data;
    X --> Q; X --> R; X --> S;