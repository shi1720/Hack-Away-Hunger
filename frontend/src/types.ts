export type Role = "admin" | "coordinator" | "driver";
export type Category = "produce" | "protein" | "dairy" | "grains" | "pantry";
export type Storage = "ambient" | "chilled" | "frozen";
export type User = {
  id: string;
  name: string;
  email: string;
  role: Role;
  network_id: string;
};
export type Auth = { user: User; csrf_token: string };
export type Site = {
  id: string;
  name: string;
  city: string;
  address: string;
  lat: number;
  lng: number;
  storage_types: Storage[];
  capacity_lb: number;
  notes: string;
  created_at: string;
};
export type Lot = {
  id: string;
  site_id: string;
  food_name: string;
  category: Category;
  storage: Storage;
  quantity_lb: number;
  reserve_lb: number;
  available_lb: number;
  expires_at: string;
  restricted: boolean;
  notes: string;
  version: number;
  created_at: string;
};
export type Need = {
  id: string;
  site_id: string;
  category: Category;
  closed: boolean;
  quantity_lb: number;
  fulfilled_lb: number;
  reserved_lb: number;
  remaining_lb: number;
  service_at: string;
  notes: string;
  created_at: string;
};
export type Status =
  | "reserved"
  | "accepted"
  | "in_transit"
  | "arrived"
  | "received"
  | "cancelled"
  | "failed";
export type Transfer = {
  id: string;
  lot_id: string;
  need_id: string;
  source_id: string;
  destination_id: string;
  food_name: string;
  category: Category;
  storage: Storage;
  quantity_lb: number;
  received_lb: number | null;
  status: Status;
  distance_miles: number;
  receiver_name: string;
  exception_reason: string;
  created_at: string;
  updated_at: string;
  service_at?: string;
  on_time?: boolean | null;
  late?: boolean;
  need_credited_lb?: number;
  failed_lb?: number;
  pickup_temperature_f: number | null;
  receipt_temperature_f: number | null;
};
export type AuditEvent = {
  id: string;
  action?: string;
  summary?: string;
  event_type?: string;
  details?: unknown;
  created_at: string;
  actor_name?: string;
  entity_type?: string;
  entity_id?: string;
};
export type Workspace = {
  user: User;
  network: { id: string; name: string; is_demo: boolean };
  sites: Site[];
  lots: Lot[];
  needs: Need[];
  transfers: Transfer[];
  events: AuditEvent[];
  metrics: {
    received_lb: number;
    active_transfers: number;
    available_lb: number;
    at_risk_lb: number;
    unmet_need_lb: number;
  };
};
export type Constraints = {
  max_distance_miles: number;
  vehicle_capacity_lb: number;
  refrigerated: boolean;
};
export type Proposal = {
  lot_id: string;
  need_id: string;
  source_id: string;
  destination_id: string;
  food_name: string;
  category: Category;
  storage: Storage;
  quantity_lb: number;
  distance_miles: number;
  score: number;
  reasons: string[];
  expires_at: string;
  service_at: string;
};
export type Plan = {
  proposals: Proposal[];
  excluded: { lot_id: string; reason: string }[];
  generated_at: string;
  assumptions: string[];
};
export type Team = {
  users: User[];
  invites: {
    role: Role;
    expires_at: string;
    used_at?: string | null;
    id?: string;
  }[];
};
export type Page =
  | "overview"
  | "planner"
  | "inventory"
  | "sites"
  | "deliveries"
  | "impact"
  | "team";
