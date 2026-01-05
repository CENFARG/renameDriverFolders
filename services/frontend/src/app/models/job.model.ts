export interface Job {
    folder_id: string;
    job_type: string;
    job_name?: string;
}

export interface JobResponse {
    status: string;
    message: string;
    job_id?: string;
    task_id?: string;
}

export interface User {
    email: string;
    name: string;
    picture: string;
}
