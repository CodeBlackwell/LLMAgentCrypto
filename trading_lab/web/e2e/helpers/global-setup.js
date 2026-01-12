/**
 * Global setup for Playwright tests
 * Detects running servers and configures fallback URLs
 */

import http from 'http';

// Port configurations - prioritize 5173 (Vite default) for Trading Lab
const PORTS = {
  api: [8000, 8001, 8080],
  web: [5173, 3000, 4173]  // Prefer 5173 first
};

/**
 * Check if a port is responding and optionally verify content
 * @param {string} host
 * @param {number} port
 * @param {string} path - Optional path to check
 * @param {string} expectedContent - Optional content to verify (for identifying correct app)
 * @returns {Promise<boolean>}
 */
async function isPortResponding(host, port, path = '/', expectedContent = null) {
  return new Promise((resolve) => {
    const options = {
      hostname: host,
      port: port,
      path: path,
      method: 'GET',
      timeout: 3000
    };

    const req = http.request(options, (res) => {
      if (res.statusCode >= 500) {
        resolve(false);
        return;
      }

      if (expectedContent) {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          resolve(data.includes(expectedContent));
        });
      } else {
        resolve(true);
      }
    });

    req.on('error', () => resolve(false));
    req.on('timeout', () => {
      req.destroy();
      resolve(false);
    });

    req.end();
  });
}

/**
 * Find the Trading Lab web server from a list of ports
 * @param {string} host
 * @param {number[]} ports
 * @returns {Promise<number|null>}
 */
async function findTradingLabPort(host, ports) {
  for (const port of ports) {
    // Check if it's the Trading Lab app by looking for the title
    const isTradingLab = await isPortResponding(host, port, '/', 'Trading Lab');
    if (isTradingLab) {
      return port;
    }
  }
  // If no Trading Lab found, return first responding port
  for (const port of ports) {
    const isResponding = await isPortResponding(host, port, '/');
    if (isResponding) {
      return port;
    }
  }
  return null;
}

/**
 * Find the API server
 * @param {string} host
 * @param {number[]} ports
 * @returns {Promise<number|null>}
 */
async function findApiPort(host, ports) {
  for (const port of ports) {
    const isHealthy = await isPortResponding(host, port, '/health', 'healthy');
    if (isHealthy) {
      return port;
    }
  }
  return null;
}

/**
 * Global setup function
 * Detects running servers and sets environment variables for tests
 */
async function globalSetup(config) {
  console.log('\n🔍 Detecting running servers...\n');

  // Use BASE_URL from environment if explicitly set
  const explicitBaseUrl = process.env.BASE_URL;
  const explicitApiUrl = process.env.API_URL;

  // Check for API server
  let apiPort = null;
  if (!explicitApiUrl) {
    apiPort = await findApiPort('localhost', PORTS.api);
    if (apiPort) {
      console.log(`✅ Trading Lab API detected on port ${apiPort}`);
      process.env.API_URL = `http://localhost:${apiPort}`;
      process.env.API_PORT = apiPort.toString();
    } else {
      console.log(`⏳ No API server detected, will start on port ${process.env.API_PORT || 8000}`);
    }
  } else {
    console.log(`📌 Using explicit API_URL: ${explicitApiUrl}`);
  }

  // Check for web server - prioritize finding Trading Lab specifically
  let webPort = null;
  if (!explicitBaseUrl) {
    webPort = await findTradingLabPort('localhost', PORTS.web);
    if (webPort) {
      console.log(`✅ Trading Lab UI detected on port ${webPort}`);
      process.env.BASE_URL = `http://localhost:${webPort}`;
      process.env.WEB_PORT = webPort.toString();
    } else {
      console.log(`⏳ No Trading Lab UI detected, will start on port ${process.env.WEB_PORT || 5173}`);
      process.env.WEB_PORT = process.env.WEB_PORT || '5173';
    }
  } else {
    console.log(`📌 Using explicit BASE_URL: ${explicitBaseUrl}`);
  }

  // Store detected configuration for tests
  const serverConfig = {
    apiUrl: process.env.API_URL || `http://localhost:${process.env.API_PORT || 8000}`,
    webUrl: process.env.BASE_URL || `http://localhost:${process.env.WEB_PORT || 5173}`,
    apiDetected: !!apiPort || !!explicitApiUrl,
    webDetected: !!webPort || !!explicitBaseUrl
  };

  console.log('\n📋 Server Configuration:');
  console.log(`   API: ${serverConfig.apiUrl} ${serverConfig.apiDetected ? '(detected/explicit)' : '(will start)'}`);
  console.log(`   Web: ${serverConfig.webUrl} ${serverConfig.webDetected ? '(detected/explicit)' : '(will start)'}`);
  console.log('');

  // Export for use in tests
  process.env.SERVER_CONFIG = JSON.stringify(serverConfig);

  return serverConfig;
}

export default globalSetup;
