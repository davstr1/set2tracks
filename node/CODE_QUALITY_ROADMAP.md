# Code Quality Improvements Roadmap

## Overview
This document tracks code quality improvements for maintainability and readability.

---

## ✅ Completed

None yet.

---

## 🔴 High Priority (Do First)

### 1. Input Validation ⏳ IN PROGRESS
**Impact:** Security + Bugs | **Effort:** Medium

**What:**
- Add express-validator to all endpoints
- Validate request bodies, query params, and route params
- Return clear error messages

**Files to update:**
- All route files (auth, set, track, channel, admin)
- Create validation middleware in `src/middleware/validation.ts`

**Implementation:**
```bash
npm install express-validator
```

---

### 2. Type Safety (Remove `any`)
**Impact:** Bugs | **Effort:** High | **Count:** 90 instances

**What:**
- Replace all `any` types with proper interfaces
- Create types for:
  - Request/Response objects
  - Job data structures
  - External API responses
  - Database query results

**Files with most `any`:**
- Controllers (casting req.user, req.query)
- Services (YouTube, Spotify API responses)
- Job processors

---

### 3. PrismaClient Singleton
**Impact:** Memory leaks | **Effort:** Low (30 mins)

**What:**
- Create single PrismaClient instance
- Export from `src/utils/database.ts`
- Update all controllers to import singleton

**Current:** 7+ controllers each create `new PrismaClient()`
**Target:** 1 shared instance

---

### 4. Custom Error Classes
**Impact:** Debugging | **Effort:** Low (1 hour)

**What:**
- Create error hierarchy in `src/utils/errors.ts`
- Classes: AppError, NotFoundError, ValidationError, AuthError
- Update global error handler middleware

---

### 5. Extract Magic Numbers
**Impact:** Maintainability | **Effort:** Low (30 mins)

**What:**
- Create `src/config/constants.ts`
- Move all magic numbers to named constants
- Categories: PAGINATION, SCHEDULER, TIMEOUTS, LIMITS

**Examples:**
- `20` → `PAGINATION.DEFAULT_PAGE_SIZE`
- `10 * 60 * 1000` → `SCHEDULER.CHANNEL_CHECK_INTERVAL_MS`

---

## 🟡 Medium Priority

### 6. Service Layer / Repository Pattern
**Impact:** Architecture | **Effort:** High (2-3 days)

**What:**
- Create repository layer for database access
- Create service layer for business logic
- Thin controllers that delegate to services

**Structure:**
```
src/
├── repositories/
│   ├── set.repository.ts
│   ├── track.repository.ts
│   └── user.repository.ts
├── services/
│   ├── set.service.ts
│   ├── track.service.ts
│   └── auth.service.ts
```

**Benefits:**
- Easier testing (mock repositories)
- Better separation of concerns
- Reusable business logic

---

### 7. DTOs (Data Transfer Objects)
**Impact:** API Contract | **Effort:** Medium (2-3 hours)

**What:**
- Define explicit types for all responses
- Create DTOs for common patterns
- Use type-safe builders

**Create:**
```
src/types/dto/
├── set.dto.ts
├── track.dto.ts
├── channel.dto.ts
├── pagination.dto.ts
└── response.dto.ts
```

---

## 🟢 Low Priority (Nice to Have)

### 8. Dependency Injection
**Impact:** Testing | **Effort:** High (3-4 days)

**What:**
- Install tsyringe or inversify
- Use DI for services, repositories, queues
- Makes unit testing easier

---

### 9. Utility Functions
**Impact:** Code Reuse | **Effort:** Low (1 hour)

**What:**
- Extract common patterns to utilities
- `parsePagination()`
- `formatResponse()`
- `parseQueryInt()`

---

### 10. Structured Logging
**Impact:** Debugging | **Effort:** Low (1 hour)

**What:**
- Always use structured logs with context
- Never use console.log
- Include request IDs

---

## 📝 TODOs to Complete

**Current TODOs in codebase:**
- [ ] `auth.controller.ts` - Send email with reset link
- [ ] `worker.ts` - Implement email processors
- [ ] `worker.ts` - Implement cleanup processors
- [ ] `scheduler.ts` - Implement cleanup scheduling
- [ ] `setProcessing.processor.ts` - Send notification email
- [ ] `shazam.service.ts` - Implement actual audio recognition (Note: This is done via recognition.service.ts)

---

## 🎯 Implementation Order

**Week 1: Quick Wins**
1. ✅ Extract constants (30 mins)
2. ✅ PrismaClient singleton (30 mins)
3. ✅ Custom error classes (1 hour)
4. ✅ Input validation (2-3 hours)

**Week 2: Type Safety**
5. ✅ Clean up `any` types (3-4 hours)
6. ✅ Add DTOs (2-3 hours)
7. ✅ Utility functions (1 hour)

**Week 3: Architecture**
8. ✅ Service layer (2-3 days)
9. ✅ Repository pattern (1-2 days)

**Week 4: Advanced**
10. ✅ Dependency injection (3-4 days)
11. ✅ Comprehensive testing setup

---

## 📊 Metrics to Track

Before improvements:
- `any` count: 90
- PrismaClient instances: 7+
- Magic numbers: ~50
- Input validation: 0%
- Test coverage: 0%

Target after improvements:
- `any` count: <10 (unavoidable edge cases)
- PrismaClient instances: 1
- Magic numbers: 0
- Input validation: 100% of endpoints
- Test coverage: >70%

---

## 🚀 Quick Start (Do These First)

```bash
# 1. Install dependencies
npm install express-validator class-validator class-transformer

# 2. Create constants file
touch src/config/constants.ts

# 3. Create error classes
touch src/utils/errors.ts

# 4. Create database singleton
touch src/utils/database.ts

# 5. Create validation middleware
touch src/middleware/validation.ts
```

---

**Last Updated:** 2025-01-05
**Status:** Starting with Input Validation (Priority 1)
