import { Injectable } from '@angular/core';

const SESSION_TOKEN_KEY = 'workshop_token';
const SESSION_USER_KEY = 'workshop_user';

@Injectable({ providedIn: 'root' })
export class SessionService {
  save(token: string, user: unknown): void {
    sessionStorage.setItem(SESSION_TOKEN_KEY, token);
    sessionStorage.setItem(SESSION_USER_KEY, String(JSON.stringify(user)));
  }

  getToken(): string | null {
    return sessionStorage.getItem(SESSION_TOKEN_KEY);
  }

  getUser(): string | null {
    return sessionStorage.getItem(SESSION_USER_KEY);
  }

  clear(): void {
    sessionStorage.removeItem(SESSION_TOKEN_KEY);
    sessionStorage.removeItem(SESSION_USER_KEY);
  }
}
