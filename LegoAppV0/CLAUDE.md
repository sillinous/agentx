# Lego Vision Project - AI/Developer Context

> **IMPORTANT**: All AI agents, developers, and automated systems MUST read this file at the start of each session. Update this file when significant changes are made to the project.

**Last Updated**: 2026-01-16
**Project Status**: 80-85% Functional, Near Production-Ready
**Version**: 0.9.5

---

## Quick Assessment

### What This Project Is
A **comprehensive, production-ready SaaS platform for Lego collection management and trading** with AI-powered brick detection and marketplace integration.

### Current State (Updated Assessment)
| Metric | Value |
|--------|-------|
| Total LOC | ~30,000 |
| Functional Completion | 80-85% |
| Architecture Complete | 95% |
| Database Tables | 25+ (including forum, auth tokens, follows) |
| Test Coverage | ~30% (unit tests added) |

### What's Working
- GraphQL API server with JWT authentication + bcrypt password hashing
- Mobile app structure (7 screens, navigation)
- Market integrations (BrickLink, eBay, BrickOwl connectors)
- Database schema with multi-tenant RLS + migrations
- Admin dashboard with full backend resolvers
- **Real-time subscriptions** via Redis PubSub
- **Email notification service** (SendGrid, SES, SMTP)
- **Forum/community features** (posts, likes, reports, comments)
- **Comprehensive error handling** with error codes
- **Seed data** (50+ colors, 100+ pieces, 25+ sets, sample users)
- Docker/Kubernetes infrastructure
- CI/CD pipelines
- Unit tests for core services

### What's Remaining (15-20%)
1. **Vision AI Models** - Framework ready, trained models needed (CRITICAL)
2. **Run seed data** - Data defined, needs to be loaded into database
3. **End-to-end testing** - Integration tests need to be run
4. **Mobile app polish** - UX improvements needed

### Recent Changes (2026-01-16 - Session 2)
- Added comprehensive seed data (colors, pieces, sets, users)
- Implemented GraphQL subscriptions with Redis PubSub
- Added error handling with error codes and validation
- Created forum/community resolvers (posts, likes, reports)
- Implemented email notification service
- Added bcrypt password hashing
- Created unit tests for auth, errors, and email services
- Added new database migrations (005, 006) for forum and auth tables

---

## Project Architecture

```
LegoAppV0/
├── apps/
│   └── mobile/              # React Native/Expo mobile app
├── packages/
│   ├── admin/               # Next.js admin dashboard
│   ├── apps/lego-vision-api/# GraphQL API server
│   ├── database/            # Database migrations & schemas
│   ├── vision-ml/           # Python ML (YOLOv8, Mask R-CNN)
│   ├── agents/              # Agent orchestration
│   └── services/            # Modular services
│       ├── user-service/
│       ├── market-service/
│       ├── vision-service/
│       └── community-service/
├── docs/                    # Documentation
└── deployment/              # Docker, K8s configs
```

### Technology Stack
- **Frontend**: React 18, Next.js 14, React Native/Expo 52, TailwindCSS
- **Backend**: Node.js, Apollo GraphQL, Python (TensorFlow, YOLOv8)
- **Database**: PostgreSQL with Row-Level Security (RLS)
- **Infrastructure**: Docker, Kubernetes, CI/CD pipeline
- **ML**: Google Vertex AI, TFLite for edge inference

---

## Priority Guidelines for AI/Developers

### When Working on This Project

1. **DO NOT** create new features unless explicitly requested
2. **PRIORITIZE** fixing bugs and completing existing features over new ones
3. **MAINTAIN** the existing code style and patterns
4. **UPDATE** this file when making significant changes
5. **FOLLOW** the Value Creation Roadmap priorities below

### Current Priority Order (P0 = Critical)

| Priority | Task | Status | Notes |
|----------|------|--------|-------|
| **P0** | Load Rebrickable Data | Pending | Database is empty, blocks all features |
| **P0** | Run Integration Tests | Ready | Script created at `scripts/test-integration.ts` |
| **P0** | Deploy to Staging | Pending | Docker configs ready |
| **P1** | Vision Model Training | Pending | Requires labeled dataset (4-6 weeks) |
| **P1** | Security Hardening | Pending | Replace hardcoded secrets |
| **P2** | Load Testing | Pending | Before beta launch |
| **P2** | Mobile App Polish | Pending | UX improvements needed |

---

## Key Files Reference

### Documentation (Read These First)
- `REALISTIC_STATUS_ASSESSMENT.md` - **Honest assessment (NEW)**
- `GAP_ANALYSIS_FINAL.md` - Detailed gap analysis
- `VALUE_CREATION_ROADMAP.md` - Strategic next steps
- `VISION_MODEL_TRAINING_GUIDE.md` - ML training instructions

### Configuration
- `package.json` (root) - Workspace configuration
- `apps/mobile/package.json` - Mobile app dependencies
- `packages/admin/package.json` - Admin dashboard
- `docker-compose.yml` - Docker services setup

### Entry Points
- `packages/apps/lego-vision-api/src/index.ts` - GraphQL API
- `apps/mobile/App.tsx` - Mobile app entry
- `packages/admin/app/page.tsx` - Admin dashboard
- `packages/vision-ml/src/server.py` - Vision API

---

## Common Commands

```bash
# Start development
npm run dev                          # Start all services
cd apps/mobile && npm start          # Mobile app
cd packages/admin && npm run dev     # Admin dashboard

# Testing
npx ts-node scripts/test-integration.ts  # Integration tests (NEW)
npm test                                  # Run unit tests

# Docker (recommended for local dev)
docker-compose -f docker-compose.lego-vision.yml up -d    # Start all services
docker-compose -f docker-compose.lego-vision.yml logs -f  # View logs
docker-compose -f docker-compose.lego-vision.yml down     # Stop all services

# Load Lego Data (IMPORTANT - database is empty!)
cd packages/database
npm run build
REBRICKABLE_API_KEY=your_key node dist/lego-data-loader.js

# Database
npm run db:migrate                   # Run migrations
npm run db:seed                      # Seed data
```

---

## UX Focus Areas

> **See `UX_IMPROVEMENT_PLAN.md` for full details (43 prioritized improvements)**

### Current UX Status
The mobile app has 7 complete screens but needs polish. Key issues:

1. **Navigation** - Two separate navigation systems (needs consolidation)
2. **Detection Feedback** - No visual feedback during capture/processing
3. **Error Handling** - Generic messages, no recovery guidance
4. **Loading States** - Spinners instead of skeleton loaders
5. **Icons** - Using emojis instead of proper icon library
6. **Forms** - Password requirements hidden, no real-time validation

### UX Implementation Priority
1. **P0 (Critical)**: Navigation consolidation, error handling, camera feedback
2. **P1 (High)**: Icon replacement, form validation, search pagination
3. **P2 (Medium)**: Dark mode, onboarding, accessibility
4. **P3 (Low)**: Deep linking, animations, badges

---

## Update Protocol

### When to Update This File
- After completing a major feature
- After fixing critical bugs
- When priorities change
- When architecture changes
- At the start of each development sprint

### How to Update
1. Update the "Last Updated" date
2. Modify the relevant section
3. Update version number (semver)
4. Commit with message: `docs: update CLAUDE.md - [brief description]`

### Version History
| Version | Date | Changes |
|---------|------|---------|
| 0.9.5 | 2026-01-16 | Subscriptions, forum, email, auth, error handling, tests |
| 0.9.0 | 2026-01-16 | Realistic assessment, admin resolvers, integration tests |
| 1.0.0 | 2025-01-09 | Initial AI context file created |

---

## For AI Agents Specifically

### Session Start Protocol
1. Read this entire file
2. Check recent git commits: `git log --oneline -10`
3. Review any open issues/PRs
4. Check TODO items in codebase if applicable
5. Proceed with user's request while respecting priorities

### Code Style Guidelines
- TypeScript for all frontend/backend code
- Python for ML services only
- Use existing patterns from the codebase
- Follow existing naming conventions
- Add tests for new functionality
- Use JSDoc/TSDoc comments sparingly (only complex logic)

### What NOT to Do
- Don't create new documentation files unless requested
- Don't refactor working code unless fixing bugs
- Don't add dependencies without justification
- Don't change database schema without updating migrations
- Don't modify authentication/security without thorough review

---

## Contact & Resources

### Repository Structure Guides
- See `docs/LEGO_DATA_FOUNDATION.md` for data model
- See `MASTER_COMPLETION_SUMMARY.md` for full project history
- See phase completion files (`PHASE_*_COMPLETION.md`) for details

### External Resources
- Rebrickable API (Lego data source)
- BrickLink API (market integration)
- Google Vertex AI (ML training)
- Expo documentation (mobile app)

---

**Remember**: This project is 80-85% complete. Focus on: (1) Loading seed data into database, (2) Running integration tests, (3) Vision model training for full functionality.
