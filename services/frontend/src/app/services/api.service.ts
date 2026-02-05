import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
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
    ) { }

    submitJob(job: Job): Observable<JobResponse> {
        const headers = this.getAuthHeaders();
        return this.http.post<JobResponse>(
            `${this.apiUrl}/api/v1/jobs/manual`,
            job,
            { headers }
        );
    }

    getJobs(): Observable<any[]> {
        const headers = this.getAuthHeaders();
        return this.http.get<any[]>(`${this.apiUrl}/api/v1/jobs`, { headers });
    }

    listJobs(): Observable<{ jobs: any[] }> {
        const headers = this.getAuthHeaders();
        return this.http.get<{ jobs: any[] }>(`${this.apiUrl}/api/v1/jobs`, { headers });
    }

    getJob(id: string): Observable<any> {
        const headers = this.getAuthHeaders();
        return this.http.get<any>(`${this.apiUrl}/api/v1/jobs/${id}`, { headers });
    }

    createJob(job: any): Observable<any> {
        const headers = this.getAuthHeaders();
        return this.http.post<any>(`${this.apiUrl}/api/v1/jobs`, job, { headers });
    }

    updateJob(id: string, job: any): Observable<any> {
        const headers = this.getAuthHeaders();
        return this.http.put<any>(`${this.apiUrl}/api/v1/jobs/${id}`, job, { headers });
    }

    deleteJob(id: string): Observable<any> {
        const headers = this.getAuthHeaders();
        return this.http.delete<any>(`${this.apiUrl}/api/v1/jobs/${id}`, { headers });
    }

    getAuditLogs(limit: number = 100): Observable<any[]> {
        const headers = this.getAuthHeaders();
        return this.http.get<any[]>(`${this.apiUrl}/api/v1/audit-logs?limit=${limit}`, { headers });
    }

    private getAuthHeaders(): HttpHeaders {
        const token = this.authService.getToken();
        return new HttpHeaders({
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        });
    }
}
