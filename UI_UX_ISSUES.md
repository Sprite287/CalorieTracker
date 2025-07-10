# CalorieTracker UI/UX Issues - Priority List

## 🔥 **CRITICAL (Fix First)**
- [x] **1. Bottom navigation overlaps content** - Content gets hidden behind fixed nav
- [x] **2. Progress bar division by zero** - App crashes if daily_calories is 0
- [x] **3. Dark mode implementation conflict** - Both documentElement and body get class, causing issues
- [x] **4. Form validation missing** - No client-side validation leads to poor UX

## ⚠️ **HIGH PRIORITY (Major UX Impact)**
- [] **5. Navigation redundancy** - Bottom nav + in-page buttons confuse users
- [ ] **6. Empty states missing** - No messaging when food database is empty
- [ ] **7. Error handling generic** - Users don't understand what went wrong
- [ ] **8. Page reload on date change** - Jarring automatic refresh experience
- [ ] **9. No loading states** - Forms submit without feedback

## 📱 **MEDIUM PRIORITY (Mobile/Polish)**
- [ ] **10. Form inputs too narrow** on mobile (92vw causes usability issues)
- [ ] **11. Duplicate viewport meta tags** - Invalid HTML
- [ ] **12. Inconsistent button styling** - Multiple classes for same purpose
- [ ] **13. Number formatting inconsistent** - No standard decimal places
- [ ] **14. Date formatting inconsistent** - Different formats across pages

## ♿ **ACCESSIBILITY (Important but not urgent)**
- [ ] **15. Color contrast insufficient** in dark mode
- [ ] **16. ARIA labels missing** for progress bars and complex elements
- [ ] **17. Form label associations** - Some inputs not properly linked
- [ ] **18. Color dependency** - Weight changes only use red/green without text
- [ ] **19. Focus management** - Skip links not positioned correctly

## 🔧 **LOW PRIORITY (Nice to Have)**
- [ ] **20. External font dependency** - FontAwesome from CDN could fail
- [ ] **21. Inline JavaScript** - Move to separate files for maintainability
- [ ] **22. Large data handling** - No pagination for big food databases
- [ ] **23. Table responsiveness** - Overly complex responsive logic
- [ ] **24. Back button inconsistency** - Some pages missing back buttons
- [ ] **25. Profile switching flow** - No quick profile switching
- [ ] **26. Flash message positioning** - Inconsistent spacing

---

## Progress Tracking
**Started:** [Date]  
**Current Focus:** Critical Issues (#1-4)  
**Completed:** 0/26  

## Notes
- Start with Critical issues for biggest impact
- Test each fix on mobile and desktop
- Verify dark mode compatibility for all changes
- Consider accessibility in every fix