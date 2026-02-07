import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { Job, JobResponse } from '../models/job.model';
import { AuthService } from './auth.service';

@Injectable({
    providedIn: 'root'
})
export class ApiService {
    private apiUrl = environment.apiUrl;

    constructor(
        private http: HttpClient,
        private authService: AuthService
    ) {
        // DEBUG: Log environment info
        console.log('🔍 ApiService initialized');
        console.log('🌍 Environment production:', environment.production);
        console.log('🔗 API URL configured:', this.apiUrl);
        console.log('📋 Full environment:', environment);
    }

    submitJob(job: Job): Observable<JobResponse> {
        const url = `${this.apiUrl}/api/v1/jobs/manual`;
        console.log('🌐 POST Request URL:', url);
        const headers = this.getAuthHeaders();
        return this.http.post<JobResponse>(url, job, { headers }).pipe(
            tap(() => console.log('✅ POST Request completed:', url))
        );
    }

    getJobs(): Observable<any[]> {
        const url = `${this.apiUrl}/api/v1/jobs`;
        console.log('🌐 GET Request URL:', url);
        const headers = this.getAuthHeaders();
        return this.http.get<any[]>(url, { headers }).pipe(
            tap(() => console.log('✅ GET Request completed:', url))
        );
    }

    listJobs(): Observable<{ jobs: any[] }> {
        const url = `${this.apiUrl}/api/v1/jobs`;
        console.log('🌐 GET Request URL (listJobs):', url);
        const headers = this.getAuthHeaders();
        return this.http.get<{ jobs: any[] }>(url, { headers }).pipe(
            tap(() => console.log('✅ GET Request completed (listJobs):', url))
        );
    }

    getJob(id: string): Observable<any> {
        const url = `${this.apiUrl}/api/v1/jobs/${id}`;
        console.log('🌐 GET Request URL (single job):', url);
        const headers = this.getAuthHeaders();
        return this.http.get<any>(url, { headers }).pipe(
            tap(() => console.log('✅ GET Request completed (single job):', url))
        );
    }

    createJob(job: any): Observable<any> {
        const headers = this.getAuthHeaders();
        return this.http.post<any>(`${this.apiUrl}/api/v1/jobs`, job, { headers });
    }

    updateJob(id: string, job: any): Observable<any> {
        const url = `${this.apiUrl}/api/v1/jobs/${id}`;
        console.log('🌐 PUT Request URL:', url);
        const headers = this.getAuthHeaders();
        return this.http.put<any>(url, job, { headers }).pipe(
            tap(() => console.log('✅ PUT Request completed:', url))
        );
    }

    deleteJob(id: string): Observable<any> {
        const url = `${this.apiUrl}/api/v1/jobs/${id}`;
        console.log('🌐 DELETE Request URL:', url);
        const headers = this.getAuthHeaders();
        return this.http.delete<any>(url, { headers }).pipe(
            tap(() => console.log('✅ DELETE Request completed:', url))
        );
    }

    getAuditLogs(limit: number = 100): Observable<{ logs: any[] }> {
        const url = `${this.apiUrl}/api/v1/audit-logs?limit=${limit}`;
        console.log('🌐 GET Request URL (audit logs):', url);
        const headers = this.getAuthHeaders();
        return this.http.get<{ logs: any[] }>(url, { headers }).pipe(
            tap(() => console.log('✅ GET Request completed (audit logs):', url))
        );
    }

    private getAuthHeaders(): HttpHeaders {
        const token = this.authService.getToken();
        return new HttpHeaders({
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        });
    }
}
