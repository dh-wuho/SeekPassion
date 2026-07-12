# Seek Passion

## 1. Introduction

### 1.1 Vision

AI Career Agent is an AI-powered career assistant that helps users discover, prepare, and submit high-quality job applications with minimal manual effort.

Unlike traditional job boards or mass auto-apply tools, AI Career Agent focuses on **quality over quantity**. The platform continuously monitors jobs from companies the user is interested in, matches those jobs against the user's career profile, generates customized application materials, and assists with browser-based applications while always allowing the user to review before submission.

The long-term vision is to build an intelligent career assistant that understands a user's professional experience as well as they do and can act on their behalf safely and efficiently.

---

### 1.2 Problem Statement

Applying for jobs is repetitive, time-consuming, and highly manual.

Typical workflow today:

* Monitor dozens of company career pages
* Read every job description
* Decide whether the position is relevant
* Edit resume for every application
* Rewrite similar application answers repeatedly
* Fill nearly identical application forms
* Track submitted applications manually

Most of these tasks are repetitive and do not require deep human creativity.

Existing solutions usually solve only one piece of the workflow:

* Job boards help discover jobs.
* Resume builders help create resumes.
* Auto-fill extensions fill forms.
* AI chatbots rewrite resumes.

Users still need to combine multiple tools and manually complete the end-to-end application process.

AI Career Agent aims to unify the complete workflow into a single platform.

---

### 1.3 Goals

#### Primary Goals

* Continuously monitor selected companies for new opportunities.
* Notify users only about relevant jobs.
* Generate truthful, customized resumes.
* Generate high-quality application answers.
* Reduce repetitive browser interactions.
* Keep users in control before final submission.
* Minimize application preparation time.

#### Secondary Goals

* Build reusable career knowledge.
* Learn from previous approved applications.
* Reduce LLM costs through reusable knowledge.
* Support multiple AI providers through BYOM.
* Create a scalable architecture for future automation.

---

### 1.4 Success Metrics

#### User Metrics

* Average application preparation time
* Resume acceptance rate
* AI answer acceptance rate
* Jobs discovered
* Applications submitted

#### Product Metrics

* Browser automation success rate
* Resume generation success rate
* Application completion rate
* Average AI cost per application
* Average browser execution time

---

## 2. Product Principles

The following principles guide all product decisions.

### 2.1 Human-in-the-Loop

The platform assists users rather than replacing them.

User review is a mandatory gate before submission for every application, with no automated bypass. The system must always stop and wait for explicit approval, regardless of match confidence or prior approvals.

The user owns the final decision.

---

### 2.2 Truthfulness

AI must never invent:

* companies
* projects
* achievements
* metrics
* technologies
* responsibilities

Every generated resume or answer must originate from verified user information stored in the system.

---

### 2.3 Knowledge First

The user's career knowledge is the single source of truth.

Instead of asking the LLM to generate content from scratch, the system should first retrieve relevant experience and then optimize its presentation.

```
Experience Library
        ↓
Retrieve Relevant Experiences
        ↓
LLM Optimization
        ↓
Resume / Answers
```

---

### 2.4 Quality Over Quantity

The objective is not to maximize the number of applications.

The objective is to maximize the quality of each application.

The system should prioritize:

* better resume matching
* better application answers
* fewer hallucinations
* higher interview probability

---

### 2.5 Modular Intelligence

Each AI capability should solve a single responsibility.

Examples include:

* Job Matching
* Resume Generation
* Question Answering
* Browser Planning
* Browser Execution

This allows individual components to improve independently over time.

---

### 2.6 Browser Independence

The browser automation layer should be replaceable.

The business logic must not depend on a specific browser framework or AI browser agent.

Possible runtimes include:

* Playwright
* browser-use
* future AI browser runtimes

---

### 2.7 Bring Your Own Model (BYOM)

Users choose which LLM provider they want to use.

The product should not require a specific AI provider.

Supported providers may include:

* OpenAI
* Anthropic
* Gemini
* GLM
* Ollama
* Future providers

---

## 3. Target Users

### 3.1 Primary Persona

#### Experienced Software Engineer

Characteristics

* 5–15 years of experience
* Applies selectively
* Interested in high-quality opportunities
* Maintains multiple resume versions
* Wants to reduce repetitive work
* Comfortable using AI tools

Typical behavior

* Monitors 20–100 companies
* Applies to 5–20 positions each month
* Customizes resumes for every application

Pain points

* Missing newly posted jobs
* Editing resumes repeatedly
* Rewriting identical answers
* Spending excessive time on application forms

---

### 3.2 Secondary Persona

#### Active Job Seeker

Characteristics

* Currently interviewing
* Applies frequently
* Wants higher application throughput
* Still values application quality

Pain points

* Managing many applications simultaneously
* Keeping resumes organized
* Tracking application progress
* Avoiding repetitive work

---

## 4. User Journey

The complete user journey consists of four major phases.

### Phase 1 — Setup

The user creates their career profile.

Steps:

1. Register or sign in.
2. Complete profile information.
3. Import an existing resume.
4. Build the Experience Library.
5. Configure AI provider.
6. Add target companies.

This setup should be completed only once.

---

### Phase 2 — Job Discovery

The platform continuously monitors target companies.

Workflow

```
Company List

↓

Job Monitoring

↓

Normalize Job

↓

Match Job

↓

Notify User
```

The user receives only relevant opportunities based on their preferences and experience.

---

### Phase 3 — Application Preparation

The user selects a job.

The system automatically:

* analyzes the job description
* retrieves relevant experiences
* generates a tailored resume
* generates application answers
* prepares required documents

The user reviews all generated content before continuing.

---

### Phase 4 — Browser-Assisted Application

After approval, the browser automation begins.

Workflow

```
Launch Browser

↓

Navigate Application

↓

Fill Profile

↓

Upload Resume

↓

Answer Questions

↓

Pause if User Input Required

↓

User Review

↓

Submit Application

↓

Record Results
```

The system should recover gracefully from navigation failures, unexpected page layouts, or new application questions whenever possible.

---

## 5. Product Pages

### 5.1 Dashboard

The Dashboard is the entry point after login and provides a high-level overview of the user's job search.

#### Objectives

* Surface newly discovered jobs
* Highlight high-match opportunities
* Show active applications
* Display pending user actions
* Provide quick navigation to the next task

#### Sections

* New Jobs
* Recommended Jobs
* Applications Requiring Review
* Recent Application Activity
* Browser Session Status
* Notifications

---

### 5.2 Companies

The Companies page manages all monitored companies.

#### Features

* Add company
* Remove company
* Enable/Disable monitoring
* Configure monitoring frequency
* View crawl history
* Trigger manual refresh

Each company stores:

* Company Name
* Career URL
* ATS Type (optional)
* Monitoring Status
* Last Crawl Time

---

### 5.3 Jobs

The Jobs page is the primary workspace.

#### Features

* Search
* Filter
* Sort
* Bookmark
* Ignore
* View Job Details
* Generate Application

#### Filters

* Company
* Location
* Role
* Level
* Employment Type
* Remote
* Posted Date
* Match Score

Each job displays:

* Company
* Position
* Location
* Posted Time
* Match Score
* Missing Skills
* Application Status

---

### 5.4 Experience Library

The Experience Library is the source of truth for all AI-generated content.

Users create reusable experience snippets.

Each snippet contains:

* Title
* Company
* Description
* Technologies
* Achievements
* Metrics
* Tags

#### Features

* Create
* Edit
* Delete
* Search
* Categorize
* AI-assisted improvement
* Duplicate detection

---

### 5.5 Resume Library

Stores every generated resume.

Features

* Preview
* Compare versions
* Download
* Regenerate
* Duplicate
* Archive

Each resume tracks:

* Target Job
* Generated Time
* Included Experience Snippets
* Resume Version

---

### 5.6 Applications

Tracks every application.

Statuses include:

* Draft
* Preparing
* Waiting Review
* Applying
* Submitted
* Failed
* Rejected
* Accepted

Displays:

* Resume Version
* Generated Answers
* Browser Logs
* Submission Time
* Application History

---

### 5.7 Browser Sessions

Provides visibility into browser automation.

Displays:

* Current Page
* Screenshot
* Action History
* Browser Logs
* Errors
* Pause/Resume
* Replay

---

### 5.8 AI Settings

Configure AI behavior.

Features

* Select Provider
* Select Model
* API Key Management
* Prompt Preferences
* Cost Statistics

---

### 5.9 Profile

Stores personal information.

Includes:

* Contact Information
* Work Authorization
* Sponsorship Requirement
* Desired Locations
* Salary Expectation
* LinkedIn
* GitHub
* Portfolio

---

### 5.10 Settings

General application settings.

Includes:

* Notifications
* Data Export
* Account Management
* Privacy
* Theme

---

## 6. Functional Requirements

### Authentication

* Email login
* Google login
* Secure session management

---

### Company Monitoring

The platform continuously monitors user-selected companies.

Responsibilities:

* Discover new jobs
* Detect updated jobs
* Remove expired jobs
* Normalize job metadata

---

### Job Discovery

The system extracts:

* Title
* Company
* Location
* Employment Type
* Level
* Description
* Posting Date
* Apply URL

Duplicate jobs should not be created.

---

### Job Matching

Input:

* User Profile
* Experience Library
* Job Description

Output:

* Match Score
* Matching Experience
* Missing Skills
* Recommendation

---

### Resume Generation

Generate customized resumes using:

* User Profile
* Experience Library
* Job Description

Requirements:

* Never hallucinate
* Preserve factual information
* Improve wording
* Reorder experiences
* Export to PDF

---

### Application Answer Generation

Generate responses for:

* Why this company?
* Leadership
* Technical
* Behavioral
* Motivation
* Custom ATS questions

Answers must originate from verified user experience.

---

### Browser-Assisted Application

The platform assists users in completing applications.

Capabilities:

* Open application page
* Navigate steps
* Upload resume
* Fill profile
* Answer questions
* Upload documents
* Save progress
* Submit application

---

### Human Review

The system must pause before submission.

Users review:

* Resume
* Generated Answers
* Salary
* Sponsorship
* Uploaded Files

Submission occurs only after explicit approval.

---

### Application Tracking

Every application stores:

* Current Status
* Resume Version
* Browser Session
* Generated Answers
* Timeline
* Browser Logs
* Screenshots

---

## 7. Core Workflows

### Workflow 1 — Company Monitoring

```text
Monitor Companies
        ↓
Retrieve Job Listings
        ↓
Normalize Jobs
        ↓
Deduplicate
        ↓
Save Jobs
        ↓
Notify User
```

---

### Workflow 2 — Job Matching

```text
Job Description
        ↓
Retrieve User Knowledge
        ↓
Calculate Match
        ↓
Generate Recommendation
```

---

### Workflow 3 — Resume Generation

```text
Job Description
        ↓
Retrieve Experience
        ↓
Generate Resume
        ↓
User Review
        ↓
Save Resume Version
```

---

### Workflow 4 — Application Preparation

```text
Selected Job
        ↓
Resume Generation
        ↓
Answer Generation
        ↓
Prepare Documents
        ↓
Ready to Apply
```

---

### Workflow 5 — Browser Application

```text
Launch Browser
        ↓
Observe Page
        ↓
Determine Action
        ↓
Execute Action
        ↓
Verify Result
        ↓
Repeat
        ↓
Pause for User Review (mandatory)
        ↓
Submit
```

---

### Workflow 6 — Application Tracking

```text
Submitted
        ↓
Record Status
        ↓
Save Browser Logs
        ↓
Save Generated Files
        ↓
Display Timeline
```

---

## 8. Job Application Harness Requirements

The Job Application Harness is responsible for executing browser-based applications.

Responsibilities include:

* Browser session management
* Navigation
* State tracking
* Retry handling
* Screenshot capture
* Logging
* Human approval checkpoints
* Browser runtime abstraction

The harness should support multiple browser runtimes without changing business logic.

It should be capable of handling:

* Unknown field ordering
* Dynamic forms
* Conditional questions
* Multi-step applications
* Different ATS platforms

### CAPTCHA / Anti-Bot Handling

When the harness encounters a CAPTCHA or other anti-bot challenge, it must pause execution and hand control to the user to resolve the challenge manually. Automated CAPTCHA-solving is out of scope for now and may be revisited in a future version.

---

## 9. Non-Functional Requirements

### Performance

* Detect newly posted jobs within 10 minutes
* Resume generation under 20 seconds
* Browser startup under 10 seconds
* Application preparation under 2 minutes

---

### Reliability

* Resume generation success >99%
* Browser workflow success >95%
* Automatic retries for recoverable failures

---

### Security

* Encrypt user data
* Encrypt AI provider credentials
* Isolate browser sessions
* Maintain audit logs

---

### Scalability

The architecture should support:

* Additional AI providers
* Additional browser runtimes
* Additional ATS integrations
* Migration from SQLite to PostgreSQL
* Horizontal scaling of browser workers

---

### Maintainability

The product should be modular.

Business logic, AI orchestration, browser automation, and persistence should remain independently replaceable.

---

## 10. Future Roadmap

### Version 1

* Company monitoring
* Job matching
* Resume generation
* Application answer generation
* Browser-assisted application
* Human review
* Application tracking
* BYOM

---

### Version 2

* More ATS integrations
* Better browser memory
* Shared resume templates
* Interview preparation
* Analytics

---

### Version 3

* Career knowledge graph
* Specialized AI models
* Autonomous application agent
* Interview assistant
* Career planning assistant

---

## 11. Success Metrics

### User Metrics

* Time spent per application
* Number of applications completed
* Resume acceptance rate
* AI answer acceptance rate
* Browser automation completion rate

---

### Product Metrics

* Jobs discovered
* Jobs matched
* Resume generation success rate
* Browser success rate
* Average AI cost per application
* Error recovery rate

---

### Business Metrics

* Monthly Active Users
* Paid Conversion Rate
* User Retention
* Interview Rate
* Offer Rate

---

## 12. MVP Scope

The MVP will include:

1. User authentication
2. User profile management
3. Experience Library
4. Company monitoring
5. Job discovery
6. Job matching
7. Resume generation
8. Application answer generation
9. Browser-assisted application
10. Human review before submission
11. Application tracking
12. Browser session management
13. BYOM support
14. Notification system

### Out of Scope (MVP)

The following features are intentionally excluded from the first release:

* Interview coaching
* Salary negotiation
* Recruiter outreach
* LinkedIn networking automation
* Cover letter optimization beyond basic generation
* Mobile applications
* Multi-user collaboration
* Fine-tuned proprietary AI models
* Fully autonomous application submission without user approval

---

## Product Summary

AI Career Agent is designed to become a user's long-term career assistant rather than a simple resume builder or auto-apply tool. The platform centralizes career knowledge, continuously discovers relevant opportunities, generates truthful and personalized application materials, and automates repetitive browser interactions while ensuring that the user remains in control of every submitted application.
