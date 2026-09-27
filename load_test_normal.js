import http from 'k6/http';
import { check, sleep } from 'k6';

// ЛР№2, Завдання 1: сценарій НОРМАЛЬНОГО навантаження на /translate
const BASE_URL = 'http://localhost:5000';
const USERNAME = __ENV.K6_USERNAME || 'testuser';
const PASSWORD = __ENV.K6_PASSWORD || 'testpass123';

export const options = {
  scenarios: {
    normal_load: {
      executor: 'constant-vus',
      vus: 5,          // 5 віртуальних користувачів
      duration: '30s',
    },
  },
  thresholds: {
    // SLO №1: p95 час відповіді /translate <= 300ms
    'http_req_duration{name:translate}': ['p(95)<300'],
    // SLO №2: частка помилок /translate < 1%
    'http_req_failed{name:translate}': ['rate<0.01'],
  },
};

export default function () {
  // Логін (форма захищена CSRF-токеном, тому спершу GET за токеном)
  const loginPage = http.get(`${BASE_URL}/auth/login`);
  const match = loginPage.body.match(/name="csrf_token" type="hidden" value="([^"]+)"/);
  const csrfToken = match ? match[1] : '';

  http.post(`${BASE_URL}/auth/login`, {
    csrf_token: csrfToken,
    username: USERNAME,
    password: PASSWORD,
  });

  // Цільовий запит — саме він вимірюється проти SLO (тег translate)
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

  sleep(0.5);
}
