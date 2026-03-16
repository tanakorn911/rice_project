วิเคราะห์ repo เดิม และสรุปว่าระบบควรถูก redesign อย่างไร เมื่อ Sentinel-2 ต้องยังคงเป็นแกนหลักของการวิเคราะห์ผลผลิต ส่วนภาพถ่ายจากมือถือทำหน้าที่เป็นข้อมูลภาคสนามสำหรับยืนยันสภาพแปลง ตำแหน่ง และสนับสนุนการบริหารจัดการห่วงโซ่อุปทานข้าว

## Part 1: วิเคราะห์ repo เดิม และ what to keep / remove / redesign
- **Keep**: rice domain, multi-role users, dashboard stats, rice field records, yield estimation concept, sale negotiation flow, role-based permissions (`users.User`, `agriculture.RiceField`, `YieldEstimation`, `SaleNotification`).
- **Remove/Reduce**: desktop-centric templates, heavy map polygon-only UX, session-first auth for mobile flow.
- **Redesign**: mobile-first field evidence flow (camera/upload + GPS), explicit verification workflow, notification center, analysis history timeline, role-based home personalization.

## Part 2: Product Architecture ใหม่
- **Mobile App (Expo RN + TS)**: auth, field record, image capture, map preview, analysis result, marketplace, notification center.
- **Django API**: role-protected REST endpoints for verification, field records/images, satellite analysis, photo analysis, yield estimation, sales, notifications.
- **Analysis services**:
  - Sentinel-2 service = primary index computation core.
  - Photo service = field verification support.
- **Async-ready**: analysis jobs can move to Celery/RQ in next phase.

## Part 3: UX/UI Direction
- Visual tone: practical, conservative, clean cards, calm colors.
- Interaction: one screen 1-2 main actions, readable statuses, large touch targets.
- Home by role:
  - FARMER: verification + latest analysis + my listings + notifications.
  - MILLER: market feed + negotiation queue.
  - GOVT: pending verification + monitoring summary.
  - ADMIN: system overview + queue health.

## Part 4: Data Model / Schema (MVP V2)
Implemented in `backend/mobile_api/models.py`:
- UserProfile
- VerificationRequest
- DeviceToken
- FieldRecord
- FieldImage
- SatelliteAnalysis
- PhotoAnalysis
- YieldEstimation
- SaleListing
- BuyRequest
- Notification
- NotificationPreference
- AuditLog

## Part 5: API Design + Backend Gaps
Implemented starter API routes under `/api/` in `backend/mobile_api/urls.py`.
- Auth: login/logout/me
- Verification: CRUD + approve action
- FieldRecord: CRUD + run_satellite_analysis + list analyses
- FieldImage: CRUD + run_photo_analysis
- Sales: CRUD + request_buy
- Notifications: list + mark_read
- Device tokens / notification preferences

**Gaps to complete**:
- JWT refresh/rotation (switch to SimpleJWT)
- forgot/reset password endpoints
- approve/reject/request-resubmission endpoints with granular policies
- push service integration (FCM/APNs)
- full stats endpoints by role

## Part 6: Mobile Navigation + Screen Flow
Starter tabs in `mobile_app/src/navigation/AppNavigator.tsx`.
Recommended production flow:
1. Splash → Welcome → Login/Register
2. Verification submission/status
3. Role-based home stack
4. Field detail with tabs: satellite trend / heatmap / images / yield / sale linkage

## Part 7: Folder Structure
- `mobile_app/src/{api,components,navigation,screens,store,types,...}`
- `backend/mobile_api/{models,serializers,views,services,urls}`

## Part 8: TypeScript Types / Interfaces
Added domain enums/interfaces in `mobile_app/src/types/domain.ts`.

## Part 9: React Native Starter Code
Added runnable starter files:
- `mobile_app/src/App.tsx`
- `mobile_app/src/navigation/AppNavigator.tsx`
- `mobile_app/src/screens/*`
- `mobile_app/src/components/PrimaryButton.tsx`
- `mobile_app/src/store/authStore.ts`
- `mobile_app/src/api/client.ts`

## Part 10: Django Backend Patch Code
Added `mobile_api` Django app with models + serializers + viewsets + urls + service modules.
Integrated app in settings and root urls.

## Part 11: Satellite Analysis Service Example
`backend/mobile_api/services/satellite.py`
- Explicitly positions Sentinel-derived indices as core outputs (NDVI/EVI/NDWI/NDRE + confidence).
- Stub is deterministic MVP and ready to replace with Google Earth Engine pipeline.

## Part 12: Photo Analysis Service Example
`backend/mobile_api/services/photo.py`
- Explicitly labels output as field verification layer.
- Returns quality/color metrics without replacing satellite-based analysis.

## Part 13: วิธีรันโปรเจกต์
1. Backend
   - `docker-compose up --build`
   - `docker-compose exec web python manage.py makemigrations mobile_api`
   - `docker-compose exec web python manage.py migrate`
2. Mobile
   - `cd mobile_app && npm install && npm run start`

## Part 14: MVP Plan และ Next Phase
**MVP**
- Login + role home
- Verification submission/review
- Field record + image upload + GPS
- Run satellite analysis + view indices
- Create sale listing + buy request
- Notification center read/unread

**Next Phase**
- Real JWT + refresh flow
- FCM/APNs push + deep links
- Earth Engine full pipeline + cloud masking + date filters
- Time-series chart + seasonal summary
- Audit log dashboards + govt monitoring map layers
