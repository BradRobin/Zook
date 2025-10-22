# Zook Vision Document

## Mission Statement
Zook is an AI-powered surveillance platform that enhances safety and enforces discipline through real-time threat detection. Starting with phone cameras and scaling to drone integration, we're building a comprehensive monitoring system for Nairobi and beyond.

## Core Philosophy: The 4D Watch System
Zook represents a **4th-dimensional surveillance approach**—a GenZ-crafted vision where AI eyes monitor live feeds 24/7 across multiple environments. Our system sees all: schools, streets, stores, and public spaces, nudging behavior toward accountability and discipline.

**The Vision**: Transform communities into safer spaces where crime, violence, and abuse fade as people adapt to responsible behavior. We believe in a watched community that grows comfortable and stronger through transparency and accountability.

## Target Markets & Applications

### 🏫 **Educational Institutions**
- **Primary Focus**: Private academies (Brookhouse, Alliance High School)
- **Use Case**: Detect aggressive gestures, bullying, and potential mistreatment
- **Value**: Protect students and create safer learning environments

### 🛒 **Retail & Commercial**
- **Primary Focus**: Shopping malls (Two Rivers), supermarkets (Naivas)
- **Use Case**: Employee theft detection, customer safety monitoring
- **Value**: Boost operational efficiency and reduce losses

### 🚌 **Transportation & Logistics**
- **Primary Focus**: Matatu fleet owners, construction sites
- **Use Case**: Remote monitoring, theft prevention, safety compliance
- **Value**: Cut operational losses and improve fleet management

### 🛡️ **Security Services**
- **Primary Focus**: Security firms (G4S Kenya)
- **Use Case**: Alert subscriptions, integrated monitoring systems
- **Value**: Enhanced security coverage and rapid response capabilities

## Technical Roadmap

### **Phase 1: MVP (Current)**
- ✅ Ultra-minimalist web UI with calculator-like design
- ✅ Live camera feed integration via `getUserMedia()`
- ✅ Simulated AI threat detection (knife detection focus)
- ✅ Authentication system with MediaMTX backend
- 🔄 Integration with YOLOv12/FastAPI at `http://localhost:8000/detect`

### **Phase 2: Scale & Integration**
- 🔄 Drone camera integration for aerial surveillance
- 🔄 WebRTC streaming via MediaMTX for real-time feeds
- 🔄 Complete authentication/login endpoint implementation
- 🔄 Multi-object detection (guns, weapons, aggressive behavior)

### **Phase 3: Enterprise Features**
- 📋 Advanced analytics dashboard
- 📋 Mobile app for security personnel
- 📋 Integration with existing security systems
- 📋 Compliance with Kenya Data Protection Act

## Success Metrics
- **Safety**: Reduction in incidents in monitored areas
- **Efficiency**: Faster threat detection and response times
- **Adoption**: Number of institutions using Zook
- **Accuracy**: AI detection confidence rates >90%

## Compliance & Ethics
- **Data Protection**: Full compliance with Kenya Data Protection Act
- **Privacy**: Local processing with minimal data retention
- **Transparency**: Clear consent mechanisms and audit trails
- **Ethics**: Focus on safety enhancement, not surveillance overreach

## References
- See [meeting notes](/docs/meeting_notes.md) for initial brainstorm (Oct 19, 2025)
- UI implementation: `/ui/src/` directory
- Backend integration: `mediamtx_authserver/` directory