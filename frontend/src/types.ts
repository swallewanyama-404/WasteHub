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
  phone_number: string | null;
  role: UserRole;
  provider_id: number | null;
  zone_id: number | null;
  client_type: string | null;
  default_address: string | null;
  default_latitude: number | null;
  default_longitude: number | null;
  collection_weekday: number;
  is_active: boolean;
  created_at?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface CollectionRequest {
  id: number;
  resident_id: number;
  zone_id: number | null;
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
  preferred_date: string | null;
  preferred_time_window: string | null;
  scheduled_at: string | null;
  completed_at: string | null;
  cancellation_reason: string | null;
  cancelled_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CollectorAssignment {
  assignment_id: number;
  request_id: number;
  provider_id: number;
  collector_id: number;
  vehicle_id: number | null;
  resident_name: string;
  resident_phone: string | null;
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

export interface Provider {
  id: number;
  name: string;
  code: string;
  contact_phone: string | null;
  contact_email: string | null;
  approval_status: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Vehicle {
  id: number;
  provider_id: number;
  zone_id: number | null;
  registration_number: string;
  vehicle_type: string;
  capacity_tons: number | null;
  status: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TrackingSession {
  id: number;
  assignment_id: number;
  vehicle_id: number;
  collector_id: number;
  started_at: string;
  ended_at: string | null;
  created_at: string;
}

export interface VehicleLocation {
  id: number;
  tracking_session_id: number;
  latitude: number;
  longitude: number;
  accuracy_meters: number | null;
  speed_kmh: number | null;
  heading_degrees: number | null;
  recorded_at: string;
  created_at: string;
}

export interface CollectorMapStop {
  assignment_id: number;
  request_id: number;
  pickup_address: string;
  pickup_latitude: number | null;
  pickup_longitude: number | null;
  assignment_status: string;
  scheduled_at: string | null;
  map_state: string;
  is_next_stop: boolean;
}

export interface CollectorOperationsMap {
  collector_id: number;
  total_stops: number;
  completed_stops: number;
  pending_stops: number;
  next_stop_assignment_id: number | null;
  stops: CollectorMapStop[];
}

export interface ResidentTimelineEvent {
  event_type: string;
  event_time: string;
  notes: string | null;
}

export interface ResidentRequestTracking {
  request_id: number;
  request_status: string;
  assignment_id: number | null;
  assignment_status: string | null;
  collector_name: string | null;
  collector_phone: string | null;
  tracking_active: boolean;
  vehicle_registration_number: string | null;
  truck_latitude: number | null;
  truck_longitude: number | null;
  distance_to_pickup_km: number | null;
  approaching: boolean;
  events: ResidentTimelineEvent[];
}

export interface Notification {
  id: number;
  user_id: number;
  notification_type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface Payment {
  id: number;
  resident_id: number;
  request_id: number | null;
  payment_type: "monthly_service" | "urgent_pickup";
  amount: string;
  currency: string;
  method: string;
  provider: string;
  status: string;
  external_reference: string;
  receipt_number: string | null;
  failure_reason: string | null;
  paid_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Complaint {
  id: number;
  resident_id: number;
  request_id: number | null;
  category: string;
  priority: string;
  description: string;
  status: string;
  resolution: string | null;
  assigned_to: number | null;
  resolved_at: string | null;
  closed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Feedback {
  id: number;
  resident_id: number;
  request_id: number;
  rating: number;
  comment: string | null;
  created_at: string;
}

export interface Evidence {
  id: number;
  assignment_id: number;
  uploaded_by: number;
  evidence_type: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
}

export interface OperationsQueueItem {
  request_id: number;
  resident_id: number;
  zone_id: number | null;
  resident_name: string;
  resident_phone: string | null;
  pickup_address: string;
  waste_type: string;
  priority: string;
  request_type: string;
  request_status: string;
  pickup_latitude: number | null;
  pickup_longitude: number | null;
  assignment_id: number | null;
  collector_id: number | null;
  provider_id: number | null;
  vehicle_id: number | null;
  assignment_status: string | null;
  created_at: string;
}

export interface CollectorWorkload {
  collector_id: number;
  full_name: string;
  email: string;
  phone_number: string | null;
  provider_id: number | null;
  zone_id: number | null;
  total_active_assignments: number;
  pending_assignments: number;
  accepted_assignments: number;
  in_progress_assignments: number;
}

export interface AvailableVehicle {
  vehicle_id: number;
  provider_id: number;
  zone_id: number | null;
  registration_number: string;
  vehicle_type: string;
  capacity_tons: number | null;
  status: string;
}

export interface AssignmentMonitoring {
  assignment_id: number;
  request_id: number;
  provider_id: number;
  collector_id: number;
  vehicle_id: number | null;
  zone_id: number | null;
  resident_name: string;
  resident_phone: string | null;
  pickup_address: string;
  waste_type: string;
  priority: string;
  assignment_status: string;
  request_status: string;
  scheduled_at: string | null;
  assigned_at: string;
  completed_at: string | null;
  is_late: boolean;
  minutes_late: number | null;
}

export interface ProviderPerformance {
  provider_id: number;
  provider_name: string;
  provider_code: string;
  total_assignments: number;
  active_assignments: number;
  completed_assignments: number;
  missed_assignments: number;
  cancelled_assignments: number;
  completion_rate_percent: number;
  missed_rate_percent: number;
}

export interface LiveVehicle {
  tracking_session_id: number;
  vehicle_id: number;
  registration_number: string;
  assignment_id: number;
  collector_id: number;
  latitude: number | null;
  longitude: number | null;
  speed_kmh: number | null;
  heading_degrees: number | null;
  recorded_at: string | null;
}

export interface AnalyticsSummary {
  total_users: number;
  residents: number;
  collectors: number;
  total_requests: number;
  completed_requests: number;
  missed_requests: number;
  active_requests: number;
  total_assignments: number;
  completed_assignments: number;
  missed_assignments: number;
  total_complaints: number;
  open_complaints: number;
  average_feedback_rating: number | null;
  total_payments: number;
  successful_payments: number;
}

export interface AuditLog {
  id: number;
  actor_id: number | null;
  action: string;
  entity_type: string;
  entity_id: number | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface RouteProgress {
  assignment_id: number;
  request_id: number;
  assignment_status: string;
  request_status: string;
  action: string;
  next_assignment_id: number | null;
  next_request_id: number | null;
  next_pickup_address: string | null;
  tracking_session_id: number | null;
  remaining_stops: number;
}

export interface Zone {
  id: number;
  name: string;
  code: string;
  municipality: string | null;
  description: string | null;
  center_latitude: number | null;
  center_longitude: number | null;
  radius_km: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ResidentServicePlan {
  client_type: string;
  default_waste_type: string;
  collection_weekday: number;
  collection_weekday_name: string;
  next_collection_date: string;
  monthly_fee_ugx: string;
  urgent_pickup_fee_ugx: string;
  month_paid: boolean;
  collection_enabled: boolean;
}

export interface ProviderFleetItem {
  registration_number: string;
  vehicle_type: string;
  capacity_tons: number | null;
  zone_id: number;
}

export interface ProviderApplication {
  id: number;
  organization_name: string;
  proposed_code: string;
  registered_address: string;
  contact_email: string;
  contact_phone: string;
  website: string | null;
  company_registration_number: string;
  tin: string;
  nema_license_number: string;
  kcca_trading_license_number: string;
  tax_clearance_reference: string;
  powers_of_attorney_reference: string;
  gazette_reference: string | null;
  years_experience: number;
  daily_capacity_tons: number;
  disposal_facility_name: string;
  disposal_facility_location: string;
  disposal_authorization_reference: string;
  monitoring_capability: string;
  client_service_hours: number;
  requested_zone_ids: number[];
  fleet: ProviderFleetItem[];
  supervisor_user_id: number;
  status: string;
  review_notes: string | null;
  reviewed_by: number | null;
  reviewed_at: string | null;
  provider_id: number | null;
  submitted_at: string;
}
