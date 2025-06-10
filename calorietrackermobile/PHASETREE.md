# 📱 Calorie Tracker Mobile App - Development Phase Tree

> **Completion Note**: Use a green boxed checkmark (✅) at the end of each phase and sub-phase to signal completion.

> **Family-First Design**: Private family health tracking with scale integration, offline support, and seamless web app compatibility.

---

## 🔍 Phase 0: Assessment & Planning
**🎯 GOAL**: Understand current system and plan minimal changes for maximum mobile value

### 0.1 Current System Analysis
- [✅] **Backend API Audit & Documentation**: Systematically identify and document all existing Flask routes (API endpoints), their HTTP methods, expected request parameters, and JSON response structures. This will be captured in a dedicated `backend_api_audit.md` file within the `calorietrackermobile` directory.
- [✅] **Database Schema Review & Documentation**: Analyze `db_handler_orm.py`, `db_orm.py`, and `models.py` to document the current database schema, including tables, columns, relationships, and data types. This will also be part of `backend_api_audit.md`.
- [✅] **Web App Compatibility Assessment**: Identify any parts of the existing web application's functionality (e.g., session management, cookie handling) that might not translate directly to a mobile API, and note potential challenges.
- [✅] **Family Data Safety - Enhanced Planning**: Detail specific procedures for creating production backups, including exact commands/scripts, storage location, frequency during development, and a clear "point of no return" definition before any database schema modifications.

### 0.2 Simplified Requirements Discovery
- **Mobile-Ready APIs**: Confirm and list the specific existing API endpoints from `backend_api_audit.md` that are suitable for direct mobile use without modification (e.g., `/api/profiles`, `/api/profile/<name>`, `/api/add_food`, `/api/food_database`, `/api/weight`, `/api/goal`, `/api/home`, `/api/summary`, `/api/history`, `/api/calorie_graph`, `/api/weight_history`).
- **Required Backend API Enhancements**: Detail the *new* or *modified* API endpoints and backend logic needed for mobile, explicitly referencing the categories from `README.md`:
    - **Authentication System**: Implement token-based authentication (e.g., using `profile_uuid` as a token in custom headers) and mobile-specific authentication middleware.
    - **Sync Infrastructure**: Add `last_modified_timestamp` fields to relevant tables and design bulk sync endpoints for efficient mobile synchronization, including conflict resolution logic.
    - **BLE Scale Data Storage**: Define API endpoints and database schema for storing high-frequency weight readings and managing weighing sessions.
    - **Mobile-Optimized Endpoints**: Identify and specify any additional endpoints or modifications for enhanced meal retrieval, bulk operations, or mobile-specific data formats.
- **Database Schema Additions**: Specify the concrete database changes required, such as adding `last_modified_timestamp` columns to existing tables and creating a new `weight_readings` table.
- **Authentication Token Details**: Formalize the token-based authentication approach, including how the `profile_uuid` will be transmitted (e.g., `X-Profile-UUID` header) and how the backend will validate it.

### 0.3 Risk Mitigation & Safety
- **Mandatory Pre-Modification Assessment**: Ensure Phase 0.1 backend assessment is fully complete before any backend modifications are initiated.
- **Incremental Backend Development**: Implement new features and modifications in a way that avoids altering existing functionality, ensuring backward compatibility with the web interface.
- **Comprehensive Data Backup Strategy**: Establish automated and verified backup procedures for the production database *before* any schema changes or data migrations, including off-site storage and verification steps (as detailed in the "Family Data Safety - Enhanced Planning" in `backend_api_audit.md`).
- **Isolated Development Environment**: Utilize an isolated development environment with a copy of family data for testing to prevent accidental impact on production data.
- **Robust Rollback Planning**: Develop and test clear procedures to revert any backend changes (code or database) to a previous stable state if issues arise.

**📋 DELIVERABLES**: Simple, safe plan to get mobile working fast

---

## 🚀 Phase 1: Flutter Foundation
**🎯 GOAL**: Master Flutter basics and set up development environment

### 1.1 Development Environment
- **Flutter SDK & IDE Setup**: Install the latest stable Flutter SDK (e.g., 3.13+ as per README) and configure the chosen IDE (Windsurf) with Flutter plugins.
- **Physical Hardware Setup**: Ensure access to and setup of the physical Decent Scale for BLE integration development and testing.
- **Initial Project Structure**: Establish a clean and maintainable project structure, considering the planned Repository Pattern and Riverpod for state management, suitable for a family application.
- **Git Repository Initialization**: Initialize and configure a Git repository for version control, ensuring proper branching strategies for mobile development.

### 1.2 Dart & Flutter Mastery
- **Dart Language Fundamentals**: Solidify understanding of Dart 3.0+ features, including null safety, asynchronous programming (async/await), and collection manipulation.
- **Flutter Widget System**: Master the core Flutter widget system, including the lifecycle of Stateless and Stateful widgets, and adherence to Material Design principles for UI/UX.
- **Navigation Patterns**: Implement simple and intuitive family-friendly navigation patterns within the app.
- **Riverpod State Management**: Gain proficiency in Riverpod 2.0+ for robust and scalable state management, preparing for its application in the family app.

### 1.3 Architecture Planning
- **Repository Pattern Definition**: Define and implement the Repository Pattern to abstract data sources, including remote API (using Dio), local database (SQLite via sqflite), and BLE (using flutter_blue_plus).
- **Model Class Design**: Design Dart model classes that precisely match backend API responses, utilizing `json_annotation` and `json_serializable` for efficient JSON serialization/deserialization with `build_runner`.
- **Robust Error Handling**: Implement a consistent and family-friendly error handling strategy for both UI feedback and internal logging.
- **Modular Code Organization**: Establish a clear and maintainable code organization structure to promote readability, reusability, and scalability for the family app.
- **Secure Data Storage**: Plan for secure storage of sensitive data like API tokens using `flutter_secure_storage`.
- **Smart Client Integration**: Design the mobile app to function as a "Smart Client," intelligently interacting with the existing web backend.

**📋 DELIVERABLES**: Working Flutter development environment ready for family app

---

## 🏗️ Phase 2: Core Infrastructure  
**🎯 GOAL**: Build solid foundation for family app functionality

### 2.1 Data Layer Foundation
- **Model Classes**: Profile, Food, Meal, WeightReading with JSON serialization
- **Local Database**: SQLite schema matching backend exactly
- **Repository Pattern**: Clean data access with family profile isolation
- **Data Validation**: Family data safety and integrity

### 2.2 Backend Integration Preparation
- **HTTP Client**: Dio setup with family-appropriate timeouts
- **API Services**: Authentication, Profile, Food, Weight, Sync services
- **Error Handling**: Retry logic for unreliable family network
- **Offline Support**: Request queuing and caching strategy

### 2.3 State Management (Riverpod)
- **Provider Setup**: Single profile per device context
- **Data Providers**: AsyncNotifier for backend data with caching
- **BLE Providers**: Scale connection and real-time data streams
- **State Persistence**: SharedPreferences + SQLite storage

### 2.4 Family-Friendly UI Framework
- **Theme System**: Large buttons, high contrast, scalable text
- **Custom Widgets**: Reusable family-friendly components
- **Navigation**: Simple bottom nav for primary functions
- **Accessibility**: Support for different family member needs

### 2.5 Developer Tools
- **Debug Menu**: Hidden 3-second press on version number
- **Logging System**: Categorized logs with export capability
- **Family Support**: One-tap data export, device identification
- **Basic Monitoring**: Sync status, BLE connection, performance

**📋 DELIVERABLES**: Robust infrastructure ready for feature development

---

## 🎯 Phase 3: Core Functionality
**🎯 GOAL**: Essential family health tracking features working end-to-end

### 3.1 Profile Management
- **Single Profile Setup**: One family member per device
- **Token Storage**: Secure local authentication storage
- **Data Caching**: Intelligent refresh and offline support
- **Developer Tools**: Manual device configuration utilities

### 3.2 Food Logging System
- **Food Search**: Cached backend database with fuzzy search
- **Meal Entry**: Breakfast, lunch, dinner, snack with portions
- **Recent Foods**: Quick access for repeated family meals
- **Offline Logging**: Sync queue with conflict resolution

### 3.3 Calorie Tracking
- **Daily Display**: Real-time counter with visual progress
- **Goal Management**: Calorie and weight goals synced with backend
- **Progress Visualization**: Family-friendly charts and indicators
- **Historical Data**: Daily, weekly, monthly family health trends

### 3.4 Synchronization
- **App Open Sync**: Pull latest data from backend
- **Background Sync**: Push changes when app closes
- **Offline Queue**: Persistent storage with retry logic
- **Family-Friendly Status**: Clear sync indicators and messaging

### 3.5 Backup & Safety
- **Data Export**: One-tap family data backup
- **Import/Restore**: Device replacement procedures
- **Auto-Backup**: Pre-update safety procedures
- **Family Guidance**: Simple recovery instructions

**📋 DELIVERABLES**: Working mobile app with essential family health tracking

---

## 🔧 Phase 4: Backend Enhancements (SIMPLIFIED)
**🎯 GOAL**: Minimal backend changes to support mobile app

### 4.1 Safety First
- **Production Backup**: Complete family data safety
- **Development Environment**: Isolated testing setup
- **Rollback Procedures**: Every change must be reversible
- **Monitoring**: Alert system for family data protection

### 4.2 Minimal Database Changes
- **Timestamps**: Add `last_modified_timestamp` to Profile & WeeklyLog
- **Scale Support**: Add `measured_weight` column to WeeklyLog  
- **Food Enhancements**: Add `food_enhancements` JSON to Profile data
- **Migration Scripts**: Safe, tested database updates

### 4.3 Simple Authentication
- **Mobile Device Table**: device_id, profile_name, access_token
- **UUID Tokens**: Simple long-lived tokens (no JWT complexity)
- **Dual Auth Middleware**: Support both web sessions AND mobile tokens
- **Profile Authorization**: Ensure family data isolation

### 4.4 API Enhancements
- **Existing Endpoint Updates**: Add mobile auth to current APIs
- **Scale Data Support**: Accept `measured_weight` in food logging
- **Food Enhancement APIs**: Manage silent nutrition improvements
- **Backward Compatibility**: Web app continues working unchanged

### 4.5 Silent Food Enhancement
- **USDA Integration**: Automatic nutrition data lookup
- **Background Processing**: Silent enhancement without user friction
- **Enhancement Storage**: Separate from user food database
- **Fallback Strategy**: Graceful handling when enhancement unavailable

### 4.6 Basic Sync System
- **Simple Endpoints**: Timestamp-based incremental sync
- **Last Write Wins**: Basic conflict resolution strategy
- **Data Types**: Profile, meals, weights, enhancements
- **Mobile-Optimized**: Efficient family data synchronization

### 4.7 Testing & Deployment
- **API Testing**: Mobile HTTP client validation
- **Web Compatibility**: Zero breaking changes confirmed
- **Family Data Testing**: Representative data validation
- **Production Deployment**: Monitored rollout with rollback ready

**📋 DELIVERABLES**: Backend ready for mobile app with minimal risk

---

## 📱 Phase 5: Advanced Features
**🎯 GOAL**: Scale integration and enhanced food recognition

### 5.1 Enhanced Food System
- **Barcode Scanning**: Camera-based product identification
- **USDA + Barcode Hybrid**: Product identity + accurate nutrition
- **Food Type Extraction**: Brand names → generic foods
- **Smart Enhancement**: Background nutrition improvement

### 5.2 BLE Scale Foundation  
- **flutter_blue_plus Setup**: Bluetooth connectivity for family devices
- **Permission Handling**: Family-friendly Bluetooth setup
- **Device Scanning**: Decent Scale detection and filtering
- **Connection Management**: Robust connect/disconnect/reconnect

### 5.3 Scale Communication
- **Decent Scale Protocol**: Command structure and real-time data
- **Weight Stream Processing**: 10Hz data handling and smoothing
- **Session Management**: Automatic weighing session detection
- **Scale Control**: Tare, zero, units with family-friendly interface

### 5.4 Scale Integration UI
- **Live Weight Display**: Large, clear family-friendly design
- **Connection Status**: Simple, understandable indicators
- **Scale Controls**: Large buttons optimized for family use
- **Session History**: Family health tracking and review

### 5.5 Advanced Data Handling
- **Weight + Food Integration**: Associate scale readings with meals
- **Enhanced Calculations**: Automatic gram-to-calorie conversion
- **Quality Assessment**: Scale data validation and reliability
- **Family Optimization**: Multiple daily weighings support

**📋 DELIVERABLES**: Professional-grade scale integration with enhanced food recognition

---

## 🎨 Phase 6: Polish & Experience
**🎯 GOAL**: Family-optimized user experience and performance

### 6.1 Animation & Interactions
- **Progress Animations**: Smooth, accessibility-aware transitions
- **Weight Display**: Clear transitions and feedback
- **Micro-Interactions**: Helpful without overwhelming family members
- **Performance Optimization**: Smooth on older family devices

### 6.2 Responsive Design
- **Multi-Device Support**: Phones, tablets, various family devices
- **Accessibility**: Text scaling, contrast, voice support
- **Theme Refinement**: Dark/light with automatic switching
- **Age-Appropriate Design**: Considerations for different family members

### 6.3 Performance Optimization
- **Widget Optimization**: Smooth rebuilds and memory efficiency
- **BLE Stability**: Reliable scale connections
- **Battery Optimization**: All-day family device usage
- **Network Efficiency**: Family data plan consideration

**📋 DELIVERABLES**: Polished, performant app optimized for family use

---

## 🔔 Phase 7: Background & Notifications
**🎯 GOAL**: Helpful, non-intrusive family notifications

### 7.1 Local Notifications
- **Gentle Reminders**: Encouraging calorie limit warnings
- **Daily Summaries**: Family routine optimization
- **Scale Battery**: Low battery notifications (if supported)
- **Sync Status**: Clear family guidance for sync issues

### 7.2 Background Processing
- **Background Sync**: Reliable when app backgrounded
- **BLE Monitoring**: Seamless scale integration
- **Data Persistence**: Family data protection on app close
- **Battery Optimization**: Extended family device usage

### 7.3 Family Peace Features
- **Simple Settings**: Minimal configuration needed
- **Do-Not-Disturb**: Family sleep and meal time respect
- **Emergency Override**: Critical health alerts only
- **Individual Customization**: Per family member preferences

**📋 DELIVERABLES**: Respectful, helpful notification system

---

## 🔄 Phase 8: Advanced Sync & Offline
**🎯 GOAL**: Robust offline support for family flexibility

### 8.1 Advanced Sync Logic
- **Intelligent Scheduling**: Family routine optimization
- **Priority Sync**: Critical data first (weight, goals)
- **Cross-Device Coordination**: Shared family data management
- **Family-Friendly Status**: Clear indicators and guidance

### 8.2 Extended Offline Support
- **Extended Operation**: Family may lack connectivity
- **Data Integrity**: Comprehensive validation and repair
- **Network Awareness**: Graceful degradation strategies
- **Family Notifications**: Offline period guidance

### 8.3 Data Protection
- **Transaction Management**: Atomic local operations
- **Privacy Protection**: Family data encryption
- **Corruption Recovery**: Automatic repair mechanisms
- **Audit Trail**: Troubleshooting support

**📋 DELIVERABLES**: Rock-solid offline support with family data protection

---

## 🏁 Phase 9: Finalization & Testing
**🎯 GOAL**: Production-ready app with family validation

### 9.1 Bug Fixes & Optimization
- **Memory Management**: Family device optimization
- **BLE Stability**: Physical scale testing and improvement
- **API Optimization**: Family network condition handling
- **Performance Tuning**: Diverse family device support

### 9.2 Family Testing
- **Beta Testing**: Real family members in daily scenarios
- **Feedback Integration**: Practical improvements based on usage
- **Accessibility Testing**: Different family member needs
- **Usage Pattern Analysis**: Practical optimization

### 9.3 Support Materials
- **Family User Guide**: Visual, clear, accessible instructions
- **Troubleshooting Guide**: Common family issues and solutions
- **Developer Documentation**: Ongoing family support procedures

**📋 DELIVERABLES**: Production-ready app validated by family use

---

## 🚀 Phase 10: Deployment
**🎯 GOAL**: Successful family rollout with ongoing support

### 10.1 Build & Distribution
- **Release Configuration**: Family device optimization
- **Signing & Security**: Secure family device deployment
- **Version Management**: Coordinated family updates

### 10.2 Family Deployment
- **Device-by-Device Setup**: Detailed configuration procedures
- **Family Member Training**: Individual device setup and training
- **Installation Verification**: Each family device validated
- **Post-Installation Testing**: Real family member validation

### 10.3 Ongoing Support
- **Direct Family Support**: Immediate developer access
- **Update Management**: Minimal family disruption
- **Device Replacement**: Family hardware change procedures
- **Continuous Improvement**: Family feedback integration

**📋 DELIVERABLES**: Successfully deployed family health tracking system

---

## 📊 Summary: Simplified vs Original Approach

| Aspect | Original Plan | Simplified Plan | Benefit |
|--------|---------------|-----------------|---------|
| **Phase 4 Complexity** | ~25 sub-phases | ~11 sub-phases | 60% reduction |
| **Database Changes** | 4 new tables + major refactoring | 2 columns + JSON structure | Minimal risk |
| **Authentication** | JWT + refresh + device registration | Simple UUID tokens | Much simpler |
| **API Development** | 15+ complex endpoints | 5 simple endpoints | Faster development |
| **Mobile Start** | After complex backend rewrite | After basic enhancements | Weeks vs months |
| **Web App Risk** | Major architectural changes | Additive enhancements only | Zero breaking changes |

**🎯 RESULT**: Get mobile app working fast while keeping all safety and family-focused benefits!