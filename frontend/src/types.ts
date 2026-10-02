export type UserRole =
  | "resident"
  | "collector"
  | "supervisor"
  | "waste_admin"
  | "system_admin";

export interface User {
  id: number;
  full_name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface CollectionRequest {
  id: number;
  resident_id: number;
  request_type: string;
  priority: string;
  status: string;
  pickup_address: string;
  pickup_latitude: number | null;
  pickup_longitude: number | null;
  waste_type: string;
  quantity_estimate: number | null;
  quantity_unit: string | null;
  reason: string | null;
  scheduled_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CollectorAssignment {
  assignment_id: number;
  request_id: number;
  provider_id: number;
  collector_id: number;
  pickup_address: string;
  waste_type: string;
  priority: string;
  assignment_status: string;
  request_status: string;
  scheduled_at: string | null;
  assigned_at: string;
  pickup_latitude: number | null;
  pickup_longitude: number | null;
}

export interface CollectorDashboard {
  collector_id: number;
  total_assignments: number;
  pending_assignments: number;
  accepted_assignments: number;
  in_progress_assignments: number;
  completed_assignments: number;
  missed_assignments: number;
  next_assignment_id: number | null;
}

export interface OrganizationDashboard {
  total_providers: number;
  active_providers: number;
  total_vehicles: number;
  available_vehicles: number;
  vehicles_on_route: number;
  vehicles_in_maintenance: number;
  active_tracking_sessions: number;
  total_assignments: number;
  pending_assignments: number;
  in_progress_assignments: number;
  completed_assignments: number;
  missed_assignments: number;
  total_collection_requests: number;
}

export interface OrganizationAlert {
  alert_id: string;
  alert_type: string;
  severity: "critical" | "high" | "medium" | "low";
  title: string;
  message: string;
  entity_type: string;
  entity_id: number;
  created_at: string;
  minutes_overdue: number | null;
}
