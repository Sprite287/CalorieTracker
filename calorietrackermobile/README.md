# CalorieTrackerMobile

## 1. Overview

CalorieTrackerMobile is a Flutter-based mobile application designed as a mobile client for the [Sprite287/CalorieTracker](https://github.com/Sprite287/CalorieTracker) web backend. This **private family application** serves less than 5 family members and provides comprehensive calorie and nutritional intake tracking, food logging, and weight management with a unique BLE integration feature.

The key innovation of this application is its direct integration with the Decent Scale via Bluetooth Low Energy (BLE) for real-time weight readings, providing a seamless weighing experience that the web interface cannot offer.

**Important Context:**
- **Private Family Use**: This application is designed exclusively for family members, with manual configuration and USB deployment by the developer.
- **No Commercial Distribution**: The app will not be distributed through app stores or commercial channels.
- **Developer-Managed**: All deployment, configuration, and maintenance is handled directly by the developer.
- **Backend Assessment Required**: **CRITICAL** - Phase 0 backend assessment must be completed before any backend modifications.

This README provides an overview of the project, its features, technology stack, setup, and development plan. The detailed, phased development plan can be found in `PHASETREE.md`.

## 2. Backend Integration Status & Requirements

### **CRITICAL: Current Backend Assessment**

The existing CalorieTracker backend provides **substantial API coverage** but requires **careful analysis and targeted modifications** for full mobile integration.

#### **✅ Existing API Capabilities (Ready for Mobile)**
The backend already includes these mobile-ready endpoints:
- **Profile Management**: GET/POST/DELETE `/api/profiles`, `/api/profile/<name>`
- **Food Logging**: POST `/api/add_food`, GET `/api/food_database/<profile>`
- **Food Database Management**: POST `/api/food_database/<profile>`, DELETE `/api/food_database/<profile>/<food_name>`
- **Meal Management**: PUT/DELETE `/api/log/<profile>/<date>/<meal_type>/<food_id>` (update/delete meal entries)
- **Weight Tracking**: GET/POST `/api/weight/<profile>`, GET `/api/weight_history/<profile>`
- **Data Retrieval**: GET `/api/home`, `/api/summary`, `/api/history/<profile>`
- **Goal Management**: GET/POST `/api/goal/<profile>`
- **Visualization Data**: GET `/api/calorie_graph/<profile>` (for charts and graphs)

#### **⚠️ Backend Modifications Required (Phase 4)**
**IMPORTANT**: These modifications are **more extensive** than initially planned and require careful implementation:

1. **Sync Infrastructure** (NEW - Critical for mobile)
   - `last_modified_timestamp` fields on all relevant tables
   - Bulk sync endpoints for efficient mobile synchronization
   - Conflict resolution logic implementation

2. **Authentication System** (NEW - Required for mobile)
   - API token generation and validation system
   - Per-device token management
   - Mobile-specific authentication middleware

3. **BLE Scale Data Storage** (NEW - For Decent Scale integration)
   - `weight_readings` table for high-frequency scale data
   - Session management for weighing events
   - Device tracking for family support

4. **Mobile-Optimized Endpoints** (Enhancement - fewer than initially planned)
   - Enhanced meal retrieval with date filtering
   - Bulk sync endpoint for efficiency
   - Mobile-specific data formats

#### **🔒 Backend Safety Requirements**
- **Zero Breaking Changes**: All modifications must maintain backward compatibility with existing web interface
- **Incremental Development**: New features added alongside existing functionality
- **Comprehensive Testing**: Full regression testing of web interface after each backend change
- **Data Integrity**: All database modifications must preserve existing family data

## 3. Key Features

*   **Family Profile Management:**
    *   Each mobile app instance is manually configured by the developer to link to a specific family member's profile on the backend.
    *   Secure local storage of profile identifiers/tokens for backend communication.
    *   No in-app profile switching needed (one device = one family member).
*   **Food Logging (Backend Integration):**
    *   Comprehensive food database interaction via the CalorieTracker backend.
    *   Log meals with details such as food items, quantities, and meal types (breakfast, lunch, dinner, snacks).
    *   Leverages existing backend food database and calorie calculation logic.
*   **Calorie and Nutritional Tracking (Backend Powered):**
    *   Automatic daily calorie calculations based on backend data.
    *   Interface for setting and monitoring calorie and weight goals (synced with backend).
    *   Visualization of progress and historical data from backend.
*   **Decent Scale BLE Integration (Mobile Innovation):**
    *   Seamless connection to Decent Scale devices using `flutter_blue_plus`.
    *   Live weight display widget with stability indicators.
    *   Functions for Tare, Zero, and other scale controls (as per Decent Scale API).
    *   Real-time weight data parsing (10Hz) and processing.
    *   Management of weighing sessions and association with food log entries.
    *   **Hardware Available**: Physical Decent Scale available for development and testing.
    *   Reference: [Decent Scale API Documentation](https://decentespresso.com/decentscale_api)
*   **Offline Capabilities:**
    *   Full offline food logging capabilities using cached backend data.
    *   Local data persistence using SQLite for profiles, food entries, and scale readings.
    *   Offline queue management for changes to be synced with the backend.
*   **Two-Way Data Synchronization:**
    *   Synchronization with the `Sprite287/CalorieTracker` web backend.
    *   **Sync Strategy:** Sync on app open (pulls data from backend) and on app close/background (pushes local changes to backend).
    *   **Conflict Resolution:** "Timestamp-based Last Write Wins" strategy handled by the backend.
*   **Family-Friendly UI/UX:**
    *   Simple, clear interface suitable for family members of all ages.
    *   Engaging animations for progress rings and weight display transitions.
    *   Custom progress indicators and animated charts/graphs.
    *   Gesture-based interactions and haptic feedback.
    *   Responsive design for multiple screen sizes and orientations.
    *   Dark/Light theme support.
*   **Developer Tools & Debugging:**
    *   Hidden developer menu for troubleshooting (accessible via long press on version).
    *   Comprehensive logging for BLE operations and backend sync.
    *   Easy data backup/restore functionality.
    *   Debug information export for remote troubleshooting.

## 4. Technology Stack

*   **Mobile Application:**
    *   Framework: Flutter (Latest Stable)
    *   Language: Dart (3.0+ with null safety)
    *   State Management: Riverpod (2.0+)
    *   HTTP Client: Dio (5.0+) for backend communication
    *   Local Database: SQLite via sqflite (3.0+) for offline caching and queueing
    *   Bluetooth Low Energy (BLE): flutter_blue_plus (1.30+)
    *   Local Storage: shared_preferences for configuration
    *   Secure Storage: flutter_secure_storage for API tokens
    *   JSON Serialization: json_annotation + json_serializable
    *   Code Generation: build_runner (for JSON serialization)
    *   Testing: Basic flutter test package for critical functions

*   **Backend Integration:**
    *   Target Backend: [Sprite287/CalorieTracker](https://github.com/Sprite287/CalorieTracker)
    *   Backend Technologies: Python 3.9+, Flask 3.1+, SQLAlchemy 2.0+, PostgreSQL
    *   API Format: RESTful JSON APIs
    *   Authentication: Token-based (to be implemented in Phase 4)

**Family App Approach:**
- **Simple & Reliable**: Focus on core functionality over complex monitoring
- **Direct Support**: Family members can report issues directly to developer
- **Manual Testing**: Real-world testing with actual family usage
- **Minimal Dependencies**: Only essential packages to reduce complexity

## 5. Project Architecture

The application follows a client-server architecture optimized for family use:

*   **Mobile Client (Flutter):** Handles user interaction, BLE communication with the Decent Scale, local data caching, and synchronization with the backend.
*   **Web Backend (`Sprite287/CalorieTracker`):** Serves as the central data repository, manages family profiles, and provides API endpoints for the mobile client.

**Key Architectural Considerations:**
*   **Backend API Enhancement**: The existing CalorieTracker backend requires **significant but carefully planned** API enhancements to support mobile client integration.
*   **Family Data Isolation**: Each mobile device is configured for a specific family member's profile, ensuring data privacy.
*   **Offline-First Design**: Mobile app functions fully offline, with periodic sync to the backend.
*   **Backward Compatibility**: All backend modifications must preserve existing web interface functionality.

Key architectural patterns used in the mobile application:

*   **Repository Pattern:** To abstract data sources (local database, remote API, and BLE).
*   **Riverpod:** For reactive state management across the application.
*   **Smart Client Pattern:** Mobile app serves as an intelligent client to the existing web backend.

## 6. Development Risk Assessment

### **High Risk Areas** ⚠️
- **Backend Modifications**: More extensive than initially planned - requires careful incremental development
- **Family Data Safety**: Zero tolerance for data loss during backend modifications
- **BLE Integration Complexity**: Hardware-dependent development with 10Hz data streams

### **Medium Risk Areas** ⚠️
- **Cross-Device Compatibility**: Multiple family Android devices with different capabilities
- **Offline Sync Edge Cases**: Conflict resolution when family members log simultaneously

### **Low Risk Areas** ✅
- **Flutter Development**: Well-documented framework with excellent tooling
- **Backend Foundation**: Existing web interface demonstrates backend stability
- **Family Scale**: Small user base reduces complexity and testing burden
- **Direct Support**: Family members can provide immediate feedback and assistance
- **Manual Testing**: Easy to test with actual family usage patterns

### **Family-Specific Advantages**
- **Immediate Feedback**: Family will report issues directly and immediately
- **Known Users**: Predictable usage patterns and device capabilities
- **Direct Debugging**: Physical access to family devices for troubleshooting
- **Flexible Deployment**: No app store requirements or review processes
- **Personal Support**: Developer available for immediate family assistance

### **Risk Mitigation Strategies**
1. **Phase 0 Mandatory**: Complete backend assessment before any modifications
2. **Incremental Backend Development**: Add features without modifying existing functionality
3. **Family Testing**: Regular testing with actual family members during development
4. **Data Backup Strategy**: Automated backups before any database modifications
5. **Rollback Plan**: Ability to revert backend changes if issues arise
6. **Direct Communication**: Immediate family feedback loop for issue resolution

## 7. Setup and Configuration (Developer Guide)

### Prerequisites

*   Flutter SDK (3.13+ recommended)
*   Android Studio or Visual Studio Code with Flutter plugins
*   Git for version control
*   Access to a configured instance of the `Sprite287/CalorieTracker` backend
*   **Physical Hardware**: Decent Scale for BLE development and testing
*   **Database Access**: Ability to create database backups and perform migrations

### **PHASE 0: Critical Backend Assessment (MANDATORY FIRST STEP)**

**⚠️ WARNING: DO NOT MODIFY BACKEND UNTIL PHASE 0 IS COMPLETE**

1. **Backend API Audit**
   ```bash
   # Document all existing API endpoints in CalorieApp.py
   # Test existing endpoints with current data
   # Map mobile app requirements to existing capabilities
   # Identify exact gaps requiring new development
   ```

2. **Database Schema Analysis**
   ```bash
   # Document current models.py structure
   # Identify tables requiring timestamp additions
   # Plan new weight_readings table structure
   # Design migration strategy with zero data loss
   ```

3. **Authentication Assessment**
   ```bash
   # Document current session-based authentication
   # Design token-based authentication for mobile
   # Plan per-device token management strategy
   # Ensure zero impact on existing web interface
   ```

4. **Data Safety Planning**
   ```bash
   # Create comprehensive backup strategy
   # Plan rollback procedures
   # Design testing approach for family data safety
   # Document migration procedures
   ```

### Backend Setup & API Development (Post-Phase 0)

1. **Backup Existing System**
   ```bash
   # Create full database backup
   # Document current API behavior
   # Create rollback procedures
   ```

2. **Incremental Backend Modifications** (Phase 4)
   - **Note**: Only proceed after Phase 0 assessment confirms scope and safety
   - Add new endpoints alongside existing ones
   - Implement timestamp infrastructure
   - Add authentication without breaking existing sessions
   - Create BLE scale data storage

### Mobile App Configuration

1. **Clone this Repository:**
    ```bash
    git clone <your-repository-url> CalorieTrackerMobile
    cd CalorieTrackerMobile
    ```
2. **Install Dependencies:**
    ```bash
    flutter pub get
    ```
3. **Family Profile Configuration:**
    *   Backend family profiles are created using the existing CalorieTracker web interface.
    *   Each mobile app instance must be manually configured with a unique profile identifier/token.
    *   Developer handles all profile setup and device configuration.
    *   No in-app profile selection needed (one device per family member).

## 8. Build and Deployment (Family Distribution)

### Building the APK

1.  Ensure your Flutter environment is correctly set up for release builds.
2.  To generate a release APK:
    ```bash
    flutter build apk --release
    ```
    The APK will be located in `build/app/outputs/flutter-apk/app-release.apk`.

### Family Device Deployment

*   **USB Installation Only**: The application is distributed exclusively via USB to family members' Android phones.
*   **Manual Configuration**: Developer configures each device with the appropriate family member's profile.
*   **Version Management**: Developer tracks app versions and coordinates updates with family members.
*   Installation process:
    ```bash
    # Enable Developer Options and USB Debugging on family member's device
    adb install path/to/your/app-release.apk
    ```

### Update Strategy

*   **Infrequent Updates Preferred**: App designed to run reliably for extended periods between updates.
*   **Backup Before Updates**: Easy data backup/restore functionality to prevent data loss during updates.
*   **Family Coordination**: Developer schedules updates with family members when convenient.

## 9. Project Development Plan

The detailed, multi-phase development plan for this application is outlined in the `PHASETREE.md` file in the root of this project. 

**⚠️ CRITICAL**: Phase 0 (Backend Assessment & Planning) is **mandatory** and must be completed before any backend modifications or Flutter development begins.

## 10. Success Metrics

*   **Family Adoption**: All family members successfully using the app daily
*   **Data Integrity**: Zero data loss during backend modifications and app updates
*   **Scale Integration**: Reliable BLE connection and accurate weight measurements
*   **Sync Reliability**: Seamless data synchronization between mobile and web interfaces
*   **Family Satisfaction**: Positive feedback and continued usage by family members

## 11. License

This project is licensed under the MIT License. See the `LICENSE` file for details.
(Note: You may need to create a `LICENSE` file with the MIT License text if one doesn't exist).
