# Project Brief

## Product Name

Annai Illam Staffing Platform

---

## What Is This App?

Annai Illam is a three-sided manpower/staffing management platform.

It helps a manpower supply company manage:

- Client companies that request workers
- Workers who are deployed to job sites
- Job requests from creation through to completion
- Worker assignments and shift scheduling
- Attendance tracking and verification
- Complaint handling and resolution

All three sides — admin, client, and worker — interact through one connected system.

---

## Who Is It For?

This app is designed for manpower and staffing companies that supply workers to:

- Factories and manufacturing plants
- Warehouses and logistics sites
- Construction sites
- Industrial client locations
- Service companies

---

## Problem Being Solved

Most manpower companies today manage operations manually.

A typical scenario:

> A client calls and says: "We need 60 workers from next Monday."

The admin team then manually:

1. Notes the request in a notebook or WhatsApp
2. Calls workers one by one to check availability
3. Assigns workers verbally or over text
4. Tracks attendance on paper or Excel
5. Handles complaints on WhatsApp
6. Updates the client through phone calls
7. Calculates salary and payment later from scattered records

**This creates real operational problems:**

- Requests get missed or misunderstood
- Workers do not show up and no one knows in advance
- Admin has no real-time visibility over what is happening on site
- Clients do not know who is assigned or whether they have checked in
- Attendance disputes arise with no record to verify against
- Complaints are not tracked and fall through the gaps
- Payments and salaries become inaccurate due to missing records

---

## Product Goal

The app should make the manpower operation:

- **Professional** — clients see a proper system, not WhatsApp messages
- **Trackable** — every assignment, check-in, and complaint is recorded
- **Reliable** — nothing falls through the cracks
- **Fast** — a client can request workers in minutes, not hours

---

## Final Outcome

When the MVP is working, the business will have:

- Faster worker request handling with clear approval flow
- Structured worker assignment replacing phone-based coordination
- GPS-verified attendance records with no disputes
- Complaint tracking from open to resolved
- Better client experience with real-time visibility
- Less dependency on WhatsApp and Excel
- A foundation that can later support payments, salary, invoices, and reports

---

## User Roles

### 1. Admin

The Admin is the manpower company's internal operations team.

They manage the entire system.

**Admin can:**

- Log in to the admin web dashboard
- Create and manage client companies
- Create and manage worker profiles
- View all job requests
- Approve or reject job requests
- Assign workers to approved jobs and shifts
- View and verify attendance records
- Mark workers as absent or late
- View and resolve complaints
- View dashboard statistics

**Admin cannot:**

- Be created by self-registration (must be invited by super-admin)
- Access the mobile app as a client or worker

---

### 2. Client

The Client is the company that hires workers through the platform.

Examples: Factory HR manager, site supervisor, warehouse operations head

**Client can:**

- Log in to the mobile app
- Create worker requests using a step-by-step form
- Save a request as a draft before submitting
- Submit a request for admin review
- View the status of their own requests
- View workers assigned to their own jobs
- View attendance status for their own jobs
- Raise complaints about workers or job quality
- Track complaint status until resolved
- View and edit their company profile

**Client cannot:**

- Access another client's data in any way
- Assign workers directly
- Change worker attendance records
- See sensitive worker personal data (bank details, full ID, etc.)
- Access admin features or the admin dashboard
- Manage salary or payments in MVP

---

### 3. Worker

The Worker is the person deployed to a job site.

**Worker can:**

- Log in to the mobile app using phone number and OTP
- View their assigned jobs
- Accept or decline a new job assignment
- View job location, shift timing, and reporting details
- Check in at the start of a shift (GPS verified)
- Check out at the end of a shift
- View their own attendance history
- Raise a complaint
- View and edit their basic profile

**Worker cannot:**

- See other workers' data or assignments
- See client billing or payment information
- Access admin features
- Modify attendance records after admin verification
- View salary automation features in MVP

---

## Core MVP Flow

```
1.  Client logs in
2.  Client creates a worker request
3.  Client submits the request
4.  Admin receives a notification
5.  Admin reviews the request
6.  Admin approves or rejects the request
7.  If approved, Admin assigns workers to shifts
8.  Workers receive job assignment notification
9.  Worker accepts or declines the job
10. On shift day, Worker checks in (GPS verified)
11. After shift, Worker checks out
12. Admin verifies the attendance record
13. Client views job and attendance status
14. Client or Worker raises a complaint if needed
15. Admin resolves or rejects the complaint
16. Job is marked completed
```

---

## Design Direction

The product should feel:

- **Modern** — clean, current UI patterns
- **Professional** — appropriate for B2B business use
- **Simple** — non-technical users should not feel lost
- **Trustworthy** — data should feel safe and accurate
- **Fast** — common actions should take seconds, not minutes

**Worker app** must be extremely simple. A worker should be able to check in within 20 seconds of opening the app.

**Client app** should feel like a professional B2B mobile product. Clean, well-spaced, informative.

**Admin web app** should be powerful and data-rich but not cluttered. Admins need to scan and act quickly.