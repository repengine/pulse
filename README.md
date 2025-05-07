## Running the Project with Docker

This project provides a Docker setup for the `context7` TypeScript service. The Docker configuration is tailored for a Node.js environment and uses a multi-stage build for efficient image size and security.

### Project-Specific Docker Requirements
- **Node.js Version:** 22.13.1 (as specified by `ARG NODE_VERSION=22.13.1` in the Dockerfile)
- **Build System:** Uses npm (with `npm ci` for deterministic installs)
- **Build Output:** The TypeScript source is built into the `dist/` directory.
- **User:** Runs as a non-root user (`appuser`) for security.
- **Environment:** `NODE_ENV=production` and `NODE_OPTIONS=--max-old-space-size=4096` are set by default.

### Environment Variables
- No required environment variables are specified in the Dockerfile or compose file by default.
- If you need to provide environment variables, you can create a `.env` file in the `./context7` directory and uncomment the `env_file` line in the `docker-compose.yml`.

### Build and Run Instructions
1. **Build and Start the Service:**
   ```sh
   docker compose up --build
   ```
   This will build the Docker image for the `context7` service and start it.

2. **Stopping the Service:**
   ```sh
   docker compose down
   ```

### Special Configuration
- **No Ports Exposed:**
  - The service does **not** expose any ports by default. It is designed to run using stdio only.
  - If you need to expose a port (e.g., to run as a network service), add a `ports:` section to the `docker-compose.yml` under the `typescript-context7` service.
- **No External Dependencies:**
  - There are no external services (databases, caches, etc.) required or configured by default.
- **Production-Ready:**
  - The image is optimized for production, with dev dependencies pruned and a non-root user.

### Example: Exposing a Port (Optional)
If your application needs to listen on a port, add the following to the `typescript-context7` service in `docker-compose.yml`:
```yaml
    ports:
      - "3000:3000"
```
And ensure your application listens on that port.

---

_This section was updated to reflect the current Docker and Docker Compose setup for the `context7` service. Please review and adjust as needed for your specific deployment or development requirements._
