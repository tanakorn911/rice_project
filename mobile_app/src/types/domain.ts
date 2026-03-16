export enum UserRole {
  FARMER = 'FARMER',
  MILLER = 'MILLER',
  GOVT = 'GOVT',
  ADMIN = 'ADMIN',
}

export enum VerificationStatus {
  NOT_SUBMITTED = 'NOT_SUBMITTED',
  PENDING = 'PENDING',
  UNDER_REVIEW = 'UNDER_REVIEW',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
  RESUBMISSION_REQUIRED = 'RESUBMISSION_REQUIRED',
}

export interface AuthUser {
  id: number;
  username: string;
  role: UserRole;
}

export interface FieldRecord {
  id: number;
  owner: number;
  name: string;
  latitude: number;
  longitude: number;
  areaRai: number;
  cropVariety?: string;
}

export interface SatelliteAnalysis {
  id: number;
  fieldRecord: number;
  analysisDate: string;
  ndviValue: number;
  eviValue: number;
  ndwiValue: number;
  ndreValue?: number;
  confidenceScore: number;
  remarks?: string;
}
