import '@angular/compiler';
import { ChangeDetectorRef, NgZone } from '@angular/core';
import { Router } from '@angular/router';
import axios, { AxiosResponse } from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { DashboardComponent } from '../dashboard/dashboard.component';
import { LoginComponent } from '../login/login.component';
import { SessionService } from './session.service';

vi.mock('axios', async (importOriginal) => {
  const actual = await importOriginal<typeof import('axios')>();
  return {
    ...actual,
    default: {
      ...actual.default,
      get: vi.fn(),
      post: vi.fn()
    }
  };
});

describe('web session flow characterization', () => {
  const localValues = new Map<string, string>();
  const sessionValues = new Map<string, string>();
  const router = { navigate: vi.fn(async () => true) } as unknown as Router;

  beforeEach(() => {
    localValues.clear();
    sessionValues.clear();
    vi.clearAllMocks();
    vi.stubGlobal('localStorage', createStorage(localValues));
    vi.stubGlobal('sessionStorage', createStorage(sessionValues));
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('stores a successful login in the tab session, loads tasks with its bearer token, and clears it on logout', async () => {
    const user = { username: 'student', displayName: 'Workshop Student' };
    vi.mocked(axios.post).mockResolvedValue({
      data: { token: 'test-token', user },
      status: 200,
      statusText: 'OK',
      headers: {},
      config: { headers: {} } as AxiosResponse['config']
    });

    const session = new SessionService();
    const loginComponent = new LoginComponent(router, session);
    loginComponent.username = 'student';
    loginComponent.password = 'Workshop123!';

    await loginComponent.login();

    expect(axios.post).toHaveBeenCalledWith(
      'http://localhost:8080/auth/login',
      { username: 'student', password: 'Workshop123!', client: 'angular-workshop' },
      { timeout: 5000 }
    );
    expect(sessionValues.get('workshop_token')).toBe('test-token');
    expect(sessionValues.get('workshop_user')).toBe(JSON.stringify(user));
    expect(localValues.has('workshop_token')).toBe(false);
    expect(localValues.has('workshop_user')).toBe(false);
    expect(localValues.has('workshop_preferences')).toBe(true);
    expect(router.navigate).toHaveBeenCalledWith(['/dashboard']);
    expect(loginComponent.busy).toBe(false);

    vi.mocked(axios.get).mockResolvedValue({
      data: [
        { title: 'Test task', description: 'Local fixture', status: 'TODO', priority: 'high', owner: 'student' },
        { title: 'Archived task', description: 'Hidden fixture', status: 'ARCHIVED', priority: 'low', owner: 'student' }
      ],
      status: 200,
      statusText: 'OK',
      headers: {},
      config: { headers: {} } as AxiosResponse['config']
    });
    const zone = { run: (callback: () => void) => callback() } as NgZone;
    const changeDetector = { detectChanges: vi.fn() } as unknown as ChangeDetectorRef;
    const dashboard = new DashboardComponent(router, changeDetector, zone, session);

    await dashboard.ngOnInit();

    expect(axios.get).toHaveBeenCalledWith(
      'http://localhost:8000/api/tasks?owner=student',
      { headers: { Authorization: 'Bearer test-token' } }
    );
    expect(dashboard.tasks).toHaveLength(2);
    expect(dashboard.visibleTasks).toHaveLength(1);
    expect(dashboard.visibleTasks[0].label).toBe('HIGH · STUDENT');
    expect(dashboard.loading).toBe(false);
    expect(dashboard.error).toBe('');

    await dashboard.logout();

    expect(sessionValues.has('workshop_token')).toBe(false);
    expect(sessionValues.has('workshop_user')).toBe(false);
    expect(localValues.has('workshop_preferences')).toBe(true);
    expect(router.navigate).toHaveBeenLastCalledWith(['/login']);
  });

  it('does not create a session or navigate when the login response has no token', async () => {
    vi.mocked(axios.post).mockResolvedValue({
      data: {},
      status: 200,
      statusText: 'OK',
      headers: {},
      config: { headers: {} } as AxiosResponse['config']
    });
    const session = new SessionService();
    const loginComponent = new LoginComponent(router, session);
    loginComponent.username = 'student';
    loginComponent.password = 'Workshop123!';

    await loginComponent.login();

    expect(sessionValues.size).toBe(0);
    expect(router.navigate).not.toHaveBeenCalled();
    expect(loginComponent.message).toContain('sin token');
  });

  it.each([
    { username: '  ', password: 'Workshop123!', expected: 'Ingrese un usuario' },
    { username: 'student', password: ' \t ', expected: 'Ingrese una contraseña' }
  ])('does not send login when required credentials are empty', async ({ username, password, expected }) => {
    const loginComponent = new LoginComponent(router, new SessionService());
    loginComponent.username = username;
    loginComponent.password = password;

    await loginComponent.login();

    expect(axios.post).not.toHaveBeenCalled();
    expect(loginComponent.message).toContain(expected);
    expect(loginComponent.busy).toBe(false);
  });

  it('shows the network error when the authentication service is unavailable', async () => {
    vi.mocked(axios.post).mockRejectedValue(new Error('Network Error'));
    const session = new SessionService();
    const loginComponent = new LoginComponent(router, session);
    loginComponent.username = 'student';
    loginComponent.password = 'Workshop123!';

    await loginComponent.login();

    expect(loginComponent.message).toContain('No se pudo autenticar a student.');
    expect(loginComponent.message).toContain('Network Error');
    expect(loginComponent.busy).toBe(false);
    expect(session.getToken()).toBeNull();
    expect(router.navigate).not.toHaveBeenCalled();
  });

  it('shows the authentication service message for a rejected login response', async () => {
    const rejection = Object.assign(new Error('Request failed with status code 401'), {
      response: { status: 401, data: { message: 'Credenciales inválidas' } }
    });
    vi.mocked(axios.post).mockRejectedValue(rejection);
    const loginComponent = new LoginComponent(router, new SessionService());
    loginComponent.username = 'student';
    loginComponent.password = 'wrong-password';

    await loginComponent.login();

    expect(loginComponent.message).toContain('Credenciales inválidas');
    expect(loginComponent.busy).toBe(false);
    expect(router.navigate).not.toHaveBeenCalled();
  });

  it('shows the timeout error and releases the login busy state', async () => {
    vi.mocked(axios.post).mockRejectedValue(new Error('timeout of 5000ms exceeded'));
    const loginComponent = new LoginComponent(router, new SessionService());
    loginComponent.username = 'student';
    loginComponent.password = 'Workshop123!';

    await loginComponent.login();

    expect(axios.post).toHaveBeenCalledWith(
      'http://localhost:8080/auth/login',
      { username: 'student', password: 'Workshop123!', client: 'angular-workshop' },
      { timeout: 5000 }
    );
    expect(loginComponent.message).toContain('timeout of 5000ms exceeded');
    expect(loginComponent.busy).toBe(false);
    expect(router.navigate).not.toHaveBeenCalled();
  });

  it('redirects to login without requesting tasks when no session token exists', async () => {
    const session = new SessionService();
    const dashboard = createDashboard(router, session);

    await dashboard.ngOnInit();

    expect(axios.get).not.toHaveBeenCalled();
    expect(router.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('shows the invalid-token response without clearing the session or redirecting', async () => {
    const session = new SessionService();
    session.save('invalid-token', { username: 'student' });
    const rejection = Object.assign(new Error('Request failed with status code 401'), {
      response: { status: 401, data: { detail: 'Token inválido' } }
    });
    vi.mocked(axios.get).mockRejectedValue(rejection);
    const dashboard = createDashboard(router, session);

    await dashboard.ngOnInit();

    expect(dashboard.error).toBe('Token inválido');
    expect(dashboard.loading).toBe(false);
    expect(session.getToken()).toBe('invalid-token');
    expect(router.navigate).not.toHaveBeenCalled();
  });

  it('shows a network error when the task service is unavailable', async () => {
    const session = new SessionService();
    session.save('test-token', { username: 'student' });
    vi.mocked(axios.get).mockRejectedValue(new Error('Network Error'));
    const dashboard = createDashboard(router, session);

    await dashboard.ngOnInit();

    expect(dashboard.error).toBe('Network Error');
    expect(dashboard.loading).toBe(false);
    expect(router.navigate).not.toHaveBeenCalled();
  });

  it('shows the caught error when a successful task response is not an array', async () => {
    const session = new SessionService();
    session.save('test-token', { username: 'student' });
    vi.mocked(axios.get).mockResolvedValue(createAxiosResponse(null));
    const dashboard = createDashboard(router, session);

    await dashboard.ngOnInit();

    expect(dashboard.error).toContain('length');
    expect(dashboard.loading).toBe(false);
  });

  it('maps known task statuses and preserves an unknown status', () => {
    const dashboard = createDashboard(router, new SessionService());

    expect(dashboard.statusLabel('TODO')).toBe('Por hacer');
    expect(dashboard.statusLabel('unknown')).toBe('unknown');
  });
});

function createDashboard(router: Router, session: SessionService): DashboardComponent {
  const zone = { run: (callback: () => void) => callback() } as NgZone;
  const changeDetector = { detectChanges: vi.fn() } as unknown as ChangeDetectorRef;
  return new DashboardComponent(router, changeDetector, zone, session);
}

function createAxiosResponse<T>(data: T): AxiosResponse<T> {
  return {
    data,
    status: 200,
    statusText: 'OK',
    headers: {},
    config: { headers: {} } as AxiosResponse<T>['config']
  };
}

function createStorage(values: Map<string, string>): Storage {
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, String(value)),
    removeItem: (key) => values.delete(key),
    clear: () => values.clear(),
    key: (index) => Array.from(values.keys())[index] ?? null,
    get length() {
      return values.size;
    }
  };
}
