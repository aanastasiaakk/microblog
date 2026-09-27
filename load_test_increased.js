import http from 'k6/http';
import { check, sleep } from 'k6';

// ЛР№2, Завдання 1: сценарій ПІДВИЩЕНОГО навантаження на /translate
// (той самий SLO, але суттєво більше одночасних користувачів ->
// демонструє реальне вузьке місце: однопотоковий Flask dev-сервер)
const BASE_URL = 'http://localhost:5000';
const USERNAME = __ENV.K6_USERNAME || 'testuser';
const PASSWORD = __ENV.K6_PASSWORD || 'testpass123';

export const options = {
  scenarios: {
    increased_load: {
      executor: 'ramping-vus',
      startVUs: 5,
      stages: [
        { duration: '10s', target: 50 },
        { duration: '20s', target: 50 },
        { duration: '10s', target: 0 },
      ],
    },
  },
  thresholds: {
    'http_req_duration{name:translate}': ['p(95)<300'],
    'http_req_failed{name:translate}': ['rate<0.01'],
  },
};

export default function () {
  const loginPage = http.get(`${BASE_URL}/auth/login`);
  const match = loginPage.body.match(/name="csrf_token" type="hidden" value="([^"]+)"/);
  const csrfToken = match ? match[1] : '';

  http.post(`${BASE_URL}/auth/login`, {
    csrf_token: csrfToken,
    username: USERNAME,
    password: PASSWORD,
  });

  const payload = JSON.stringify({
    text: 'Hello world',
    source_language: 'en',
    dest_language: 'uk',
  });
  const res = http.post(`${BASE_URL}/translate`, payload, {
    headers: { 'Content-Type': 'application/json' },
    tags: { name: 'translate' },
  });

  check(res, { 'status is 200': (r) => r.status === 200 });

  sleep(0.2);
}
