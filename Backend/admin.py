from database import SessionLocal
import secrets
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from models import (
    Voter,
    Election,
    Candidate,
    CandidateNomination,
    CandidateProfile,
    VotingRecord,
    Vote,
    Election
)


from admin_auth import require_admin
from blockchain import add_candidate_to_blockchain

router = APIRouter()


# ============================================================
# DATABASE
# ============================================================

def get_db():
    return SessionLocal()


# ============================================================
# FLASH MESSAGES
# ============================================================

def set_flash(request: Request, message: str):
    request.session["flash_message"] = message


def get_flash(request: Request):
    return request.session.pop("flash_message", None)


def csrf_input(request: Request) -> str:
    """Return a hidden CSRF field backed by the current admin session."""
    token = request.session.get("admin_review_csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["admin_review_csrf"] = token
    return f'<input type="hidden" name="csrf_token" value="{safe(token)}">'


# ============================================================
# HTML ESCAPING
# ============================================================

def safe(value):
    """
    Basic HTML escaping for values displayed in the admin panel.
    """

    if value is None:
        return ""

    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )


# ============================================================
# PAGE TEMPLATE
# ============================================================

def page_template(
    title,
    content,
    message=None,
    active_page="dashboard"
):

    message_html = ""

    if message:
        message_html = f"""
        <div class="flash-message">
            <div class="flash-icon">✓</div>
            <div>{safe(message)}</div>
        </div>
        """

    active = {
        "dashboard": "",
        "voters": "",
        "elections": "",
        "candidates": "",
        "nominations": "",
        "results": ""
    }

    if active_page in active:
        active[active_page] = "active"

    return f"""
<!DOCTYPE html>

<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>{safe(title)} | GZU Voting</title>

    <style>

        * {{
            box-sizing: border-box;
        }}

        html {{
            font-size: 16px;
        }}

        :root {{
            --gzu-green: #087f3e;
            --gzu-dark: #075c2e;
            --gzu-light: #e9f7ef;
            --sidebar: #092b1b;
            --sidebar-hover: #10462d;
            --background: #f4f7f6;
            --white: #ffffff;
            --text: #1f2937;
            --muted: #6b7280;
            --border: #e5e7eb;
            --danger: #dc3545;
            --warning: #f59e0b;
            --success: #198754;
            --shadow: 0 4px 18px rgba(0, 0, 0, 0.06);
        }}

        body {{
            margin: 0;

            font-family:
                Inter,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                Arial,
                sans-serif;

            background: var(--background);
            color: var(--text);

            font-size: 16px;
            line-height: 1.5;
        }}

        a {{
            text-decoration: none;
        }}


        /* ====================================================
           SIDEBAR
           ==================================================== */

        .sidebar {{

            position: fixed;

            left: 0;
            top: 0;
            bottom: 0;

            width: 250px;

            display: flex;
            flex-direction: column;

            background:
                linear-gradient(
                    180deg,
                    #082d1b 0%,
                    #061f13 100%
                );

            color: white;

            z-index: 1000;

            overflow-y: auto;

            box-shadow:
                4px 0 20px rgba(0,0,0,0.08);
        }}


        .brand {{

            min-height: 88px;
            box-sizing: border-box;

            display: flex;
            align-items: center;
            justify-content: flex-start;

            gap: 14px;
            padding: 12px 22px;

            border-bottom:
                1px solid rgba(255,255,255,0.08);
        }}


        .brand-logo {{

            width: 42px;
            height: 42px;

            border-radius: 50%;

            background: white;

            color: var(--gzu-green);

            display: flex;

            align-items: center;
            justify-content: center;

            font-weight: 800;

            font-size: 15px;

            box-shadow:
                0 3px 10px rgba(0,0,0,0.2);
        }}


        .brand-text {{
            line-height: 1.2;
        }}


        .brand-title {{
            font-size: 18px;
            font-weight: 700;
        }}


        .brand-subtitle {{
            font-size: 13px;
            color: #9ac5ad;
            margin-top: 3px;
        }}


        .sidebar-section-title {{

            padding:
                24px 22px 9px;

            font-size: 12px;

            font-weight: 700;

            color: #78a68c;

            text-transform: uppercase;

            letter-spacing: 1px;
        }}


        .nav {{
            padding: 0 12px;
        }}


        .nav-link {{

            display: flex;

            align-items: center;

            gap: 13px;

            padding:
                13px 14px;

            margin-bottom: 4px;

            color: #c7d8cf;

            border-radius: 8px;

            font-size: 16px;

            font-weight: 500;

            transition:
                background 0.2s,
                color 0.2s;
        }}


        .nav-link:hover {{
            background: var(--sidebar-hover);
            color: white;
        }}


        .nav-link.active {{

            background:
                linear-gradient(
                    90deg,
                    var(--gzu-green),
                    #0b9a4c
                );

            color: white;

            box-shadow:
                0 4px 12px rgba(8,127,62,0.25);
        }}


        .nav-icon {{

            width: 22px;

            text-align: center;

            font-size: 19px;
        }}


        .sidebar-footer {{

            position: static;

            margin-top: auto;
            flex-shrink: 0;

            left: 0;
            right: 0;

            padding: 16px;

            border-top:
                1px solid rgba(255,255,255,0.08);
        }}


        .logout-link {{

            display: flex;

            align-items: center;

            gap: 12px;

            padding: 12px 14px;

            border-radius: 8px;

            color: #e4b7b7;

            font-size: 16px;
        }}


        .logout-link:hover {{
            background: rgba(220,53,69,0.12);
            color: #ffaaaa;
        }}


        /* ====================================================
           MAIN
           ==================================================== */

        .main {{

            margin-left: 250px;

            min-height: 100vh;
        }}


        /* ====================================================
           TOP BAR
           ==================================================== */

        .topbar {{

            height: 80px;

            background: white;

            border-bottom:
                1px solid var(--border);

            display: flex;

            align-items: center;

            justify-content: space-between;

            padding:
                0 32px;

            position: sticky;

            top: 0;

            z-index: 500;
        }}


        .topbar-left {{

            display: flex;

            align-items: center;

            gap: 15px;
        }}


        .page-title {{

            margin: 0;

            font-size: 22px;

            font-weight: 700;

            color: #17251d;
        }}


        .topbar-subtitle {{

            margin: 4px 0 0;

            font-size: 14px;

            color: var(--muted);
        }}


        .admin-profile {{

            display: flex;

            align-items: center;

            gap: 10px;
        }}


        .admin-avatar {{

            width: 42px;
            height: 42px;

            border-radius: 50%;

            background: var(--gzu-light);

            color: var(--gzu-green);

            display: flex;

            align-items: center;
            justify-content: center;

            font-weight: 700;

            font-size: 14px;
        }}


        .admin-name {{

            font-size: 15px;

            font-weight: 600;

            color: #374151;
        }}


        .admin-role {{

            font-size: 13px;

            color: var(--muted);

            margin-top: 2px;
        }}


        /* ====================================================
           CONTENT
           ==================================================== */

        .content {{

            padding: 30px 32px;

            max-width: 1500px;

            margin: 0 auto;
        }}


        .flash-message {{

            background: #eaf8ef;

            border:
                1px solid #c8ead5;

            color: #166534;

            padding: 14px 18px;

            border-radius: 9px;

            display: flex;

            align-items: center;

            gap: 10px;

            margin-bottom: 22px;

            font-size: 15px;

            font-weight: 600;
        }}


        .flash-icon {{

            width: 25px;
            height: 25px;

            border-radius: 50%;

            background: #198754;

            color: white;

            display: flex;

            align-items: center;
            justify-content: center;

            font-size: 14px;
        }}


        .page-heading {{

            display: flex;

            justify-content: space-between;

            align-items: center;

            gap: 15px;

            flex-wrap: wrap;

            margin-bottom: 25px;
        }}


        .page-heading h1,
        .page-heading h2 {{

            margin: 0;

            font-size: 25px;

            color: #17251d;
        }}


        .page-heading p {{

            margin: 6px 0 0;

            color: var(--muted);

            font-size: 15px;
        }}

        .nominations-page-heading h1 {{
            line-height: 1.25;
        }}


        /* ====================================================
           STATISTICS
           ==================================================== */

        .stats-grid {{

            display: grid;

            grid-template-columns:
                repeat(4, minmax(0, 1fr));

            gap: 18px;

            margin-bottom: 25px;
        }}


        .stat-card {{

            background: white;

            border:
                1px solid var(--border);

            border-radius: 12px;

            padding: 21px;

            box-shadow: var(--shadow);

            position: relative;

            overflow: hidden;
        }}


        .stat-card::after {{

            content: "";

            position: absolute;

            right: -30px;
            top: -30px;

            width: 90px;
            height: 90px;

            border-radius: 50%;

            background: var(--gzu-light);
        }}


        .stat-top {{

            display: flex;

            align-items: center;

            justify-content: space-between;
        }}


        .stat-icon {{

            width: 46px;
            height: 46px;

            border-radius: 9px;

            background: var(--gzu-light);

            color: var(--gzu-green);

            display: flex;

            align-items: center;
            justify-content: center;

            font-size: 21px;
        }}


        .stat-card h3 {{

            margin:
                15px 0 4px;

            font-size: 15px;

            color: var(--muted);

            font-weight: 600;
        }}


        .stat-card strong {{

            font-size: 32px;

            color: #17251d;

            font-weight: 750;
        }}


        /* ====================================================
           CARDS
           ==================================================== */

        .card {{

            background: white;

            border:
                1px solid var(--border);

            border-radius: 12px;

            box-shadow: var(--shadow);

            margin-bottom: 22px;

            overflow: hidden;
        }}


        .card-header {{

            padding:
                20px 22px;

            border-bottom:
                1px solid var(--border);

            display: flex;

            align-items: center;

            justify-content: space-between;

            gap: 15px;

            flex-wrap: wrap;
        }}


        .card-header h3 {{

            margin: 0;

            font-size: 18px;

            color: #17251d;
        }}


        .card-header span {{

            font-size: 14px;

            color: var(--muted);

        }}


        .card-body {{
            padding: 22px;
        }}


        .card-body p {{
            font-size: 15px;
            line-height: 1.6;
        }}


        /* ====================================================
           DASHBOARD QUICK ACTIONS
           ==================================================== */

        .quick-grid {{

            display: grid;

            grid-template-columns:
                repeat(4, minmax(0, 1fr));

            gap: 18px;

            margin-bottom: 25px;
        }}


        .quick-card {{

            background: white;

            border:
                1px solid var(--border);

            border-radius: 12px;

            padding: 22px;

            box-shadow: var(--shadow);

            transition:
                transform 0.2s,
                box-shadow 0.2s;
        }}


        .quick-card:hover {{

            transform:
                translateY(-3px);

            box-shadow:
                0 8px 24px
                rgba(0,0,0,0.09);
        }}


        .quick-icon {{

            width: 48px;
            height: 48px;

            border-radius: 10px;

            background: var(--gzu-light);

            color: var(--gzu-green);

            display: flex;

            align-items: center;
            justify-content: center;

            font-size: 22px;

            margin-bottom: 15px;
        }}


        .quick-card h3 {{

            margin:
                0 0 7px;

            font-size: 17px;
        }}


        .quick-card p {{

            margin:
                0 0 17px;

            color: var(--muted);

            font-size: 15px;

            line-height: 1.6;
        }}


        /* ====================================================
           BUTTONS
           ==================================================== */

        .button {{

            display: inline-flex;

            align-items: center;

            justify-content: center;

            gap: 7px;

            background:
                linear-gradient(
                    135deg,
                    #087f3e,
                    #0b9a4c
                );

            color: white;

            padding:
                11px 16px;

            border-radius: 7px;

            text-decoration: none;

            border: none;

            cursor: pointer;

            font-size: 14px;

            font-weight: 600;

            transition:
                transform 0.15s,
                box-shadow 0.15s;
        }}


        .button:hover {{

            color: white;

            transform:
                translateY(-1px);

            box-shadow:
                0 5px 12px
                rgba(8,127,62,0.2);
        }}


        .button-secondary {{

            background:
                #6b7280;
        }}


        .button-secondary:hover {{
            background: #4b5563;
        }}


        .button-danger {{

            background:
                #dc3545;
        }}


        .button-danger:hover {{
            background: #b02a37;
        }}


        .button-light {{

            background: #eef2f0;

            color: #374151;

            box-shadow: none;
        }}


        .button-light:hover {{

            background: #dfe7e2;

            color: #17251d;

            box-shadow: none;
        }}

        .button {{
            min-height: 40px;
            min-width: 88px;
            padding: 10px 18px;
            border-radius: 9px;
            font-size: 14px;
            line-height: 1.2;
            white-space: nowrap;
            box-sizing: border-box;
        }}

        .button-danger {{
            background: linear-gradient(135deg, #d92d43, #e54858);
        }}

        .button-danger:hover {{
            background: linear-gradient(135deg, #b42335, #d92d43);
            box-shadow: 0 5px 12px rgba(217, 45, 67, 0.18);
        }}

        .action-buttons {{
            display: flex;
            align-items: center;
            justify-content: flex-start;
            flex-wrap: wrap;
            gap: 10px;
            min-width: 190px;
        }}

        .action-buttons form {{
            display: inline-flex;
            margin: 0;
            padding: 0;
        }}

        .action-buttons .button {{
            min-width: 84px;
        }}

        @media (max-width: 640px) {{
            .action-buttons {{
                gap: 8px;
            }}
            .action-buttons .button {{
                min-width: 78px;
                padding: 9px 13px;
            }}
        }}



        /* ====================================================
           TABLES
           ==================================================== */

        .table-wrapper {{
            overflow-x: auto;
        }}


        table {{

            width: 100%;

            border-collapse: collapse;

            min-width: 650px;
        }}


        th,
        td {{

            padding:
                15px 16px;

            text-align: left;

            border-bottom:
                1px solid #edf0ee;

            font-size: 15px;

            line-height: 1.5;
        }}


        th {{

            background: #f7faf8;

            color: #526158;

            font-size: 12px;

            text-transform: uppercase;

            letter-spacing: 0.5px;

            font-weight: 700;
        }}


        tbody tr:hover {{
            background: #fafcfb;
        }}


        tbody tr:last-child td {{
            border-bottom: none;
        }}


        /* ====================================================
           FORMS
           ==================================================== */

        .form-card {{

            max-width: 750px;

            background: white;

            border:
                1px solid var(--border);

            border-radius: 12px;

            padding: 28px;

            box-shadow: var(--shadow);
        }}


        .form-card h2 {{

            margin:
                0 0 6px;

            font-size: 23px;
        }}


        .form-description {{

            color: var(--muted);

            font-size: 15px;

            margin-bottom: 25px;

            line-height: 1.6;
        }}


        label {{

            display: block;

            font-weight: 600;

            font-size: 15px;

            margin:
                18px 0 7px;

            color: #374151;
        }}


        input,
        select,
        textarea {{

            width: 100%;

            padding:
                12px 14px;

            border:
                1px solid #d5ddd8;

            border-radius: 7px;

            font-size: 15px;

            color: #1f2937;

            background: white;

            outline: none;

            transition:
                border 0.2s,
                box-shadow 0.2s;
        }}


        input::placeholder,
        textarea::placeholder {{
            color: #9ca3af;
            font-size: 14px;
        }}


        input:focus,
        select:focus,
        textarea:focus {{

            border-color:
                var(--gzu-green);

            box-shadow:
                0 0 0 3px
                rgba(8,127,62,0.10);
        }}


        textarea {{

            min-height: 110px;

            resize: vertical;
        }}


        .form-actions {{

            display: flex;

            gap: 10px;

            margin-top: 25px;

            flex-wrap: wrap;
        }}


        /* ====================================================
           SEARCH
           ==================================================== */

        .search-panel {{

            background: white;

            border:
                1px solid var(--border);

            border-radius: 12px;

            padding: 18px;

            margin-bottom: 22px;

            box-shadow: var(--shadow);
        }}


        .search-row {{

            display: grid;

            grid-template-columns:
                2fr 1fr auto;

            gap: 10px;
        }}


        /* ====================================================
           STATUS
           ==================================================== */

        .status {{

            display: inline-flex;

            align-items: center;

            gap: 6px;

            padding:
                7px 11px;

            border-radius: 30px;

            font-size: 12px;

            font-weight: 800;

            letter-spacing: 0.4px;
        }}


        .status::before {{

            content: "";

            width: 7px;
            height: 7px;

            border-radius: 50%;

            background: currentColor;
        }}


        .status-upcoming {{

            background: #fff7df;

            color: #9a6700;
        }}


        .status-ongoing {{

            background: #e7f7ed;

            color: #18713b;
        }}


        .status-closed {{

            background: #fdebed;

            color: #a61e2a;
        }}


        .status-unknown {{

            background: #eef0f1;

            color: #596168;
        }}


        /* ====================================================
           ELECTION CARDS
           ==================================================== */

        .election-card {{

            background: white;

            border:
                1px solid var(--border);

            border-radius: 12px;

            padding: 21px;

            margin-bottom: 15px;

            box-shadow: var(--shadow);
        }}


        .election-header {{

            display: flex;

            justify-content: space-between;

            align-items: center;

            gap: 15px;

            flex-wrap: wrap;
        }}


        .election-header h3 {{

            margin: 0;

            font-size: 19px;

            color: #17251d;
        }}


        .election-meta {{

            color: var(--muted);

            font-size: 14px;

            margin-top: 5px;
        }}


        .election-description {{

            color: #66736b;

            font-size: 15px;

            line-height: 1.6;

            margin:
                14px 0;
        }}


        .action-row {{

            display: flex;

            gap: 8px;

            flex-wrap: wrap;

            margin-top: 15px;
        }}


        /* ====================================================
           BACK LINK
           ==================================================== */

        .back-link {{

            display: inline-flex;

            align-items: center;

            gap: 6px;

            color: var(--gzu-green);

            font-size: 15px;

            font-weight: 600;

            margin-bottom: 20px;
        }}


        .back-link:hover {{
            color: var(--gzu-dark);
        }}


        /* ====================================================
           EMPTY STATE
           ==================================================== */

        .empty-state {{

            text-align: center;

            padding: 45px 20px;

            color: var(--muted);

            font-size: 15px;
        }}


        .empty-state h2 {{
            font-size: 22px;
            color: #17251d;
        }}


        .empty-state p {{
            font-size: 15px;
        }}


        .empty-icon {{

            font-size: 38px;

            margin-bottom: 10px;
        }}


        /* ====================================================
           MOBILE
           ==================================================== */

        .mobile-menu {{

            display: none;

            border: none;

            background: transparent;

            font-size: 26px;

            cursor: pointer;

            color: #17251d;
        }}


        @media(max-width: 1100px) {{

            .stats-grid {{
                grid-template-columns:
                    repeat(2, 1fr);
            }}

            .quick-grid {{
                grid-template-columns:
                    repeat(2, 1fr);
            }}

        }}


        @media(max-width: 800px) {{

            .sidebar {{

                transform:
                    translateX(-100%);

                transition:
                    transform 0.25s ease;
            }}


            .sidebar.open {{

                transform:
                    translateX(0);
            }}


            .main {{
                margin-left: 0;
            }}


            .mobile-menu {{
                display: block;
            }}


            .topbar {{
                padding:
                    0 18px;
            }}


            .content {{
                padding:
                    22px 18px;
            }}

        }}


        @media(max-width: 600px) {{

            .stats-grid,
            .quick-grid {{
                grid-template-columns: 1fr;
            }}


            .admin-name,
            .admin-role {{
                display: none;
            }}


            .search-row {{
                grid-template-columns: 1fr;
            }}


            .page-heading h2 {{
                font-size: 22px;
            }}

        }}

    </style>

</head>


<body>


<!-- ========================================================
     SIDEBAR
     ======================================================== -->

<aside
    class="sidebar"
    id="sidebar"
>

    <div class="brand">

        <div class="brand-logo">
            GZU
        </div>

        <div class="brand-text">

            <div class="brand-title">
                GZU Voting
            </div>

            <div class="brand-subtitle">
                Administration Panel
            </div>

        </div>

    </div>


    <div class="sidebar-section-title">
        Main Menu
    </div>


    <nav class="nav">

        <a
            href="/admin"
            class="nav-link {active["dashboard"]}"
        >

            <span class="nav-icon">⌂</span>

            <span>Dashboard</span>

        </a>


        <a
            href="/admin/voters"
            class="nav-link {active["voters"]}"
        >

            <span class="nav-icon">♙</span>

            <span>Voters</span>

        </a>


        <a
            href="/admin/elections"
            class="nav-link {active["elections"]}"
        >

            <span class="nav-icon">▣</span>

            <span>Elections</span>

        </a>


        <a
            href="/admin/candidates"
            class="nav-link {active["candidates"]}"
        >

            <span class="nav-icon">♟</span>

            <span>Candidates</span>

        </a>


        <a
            href="/admin/nominations"
            class="nav-link {active["nominations"]}"
        >
            <span class="nav-icon">✓</span>
            <span>Candidate Nominations</span>
        </a>

        <a
            href="/admin/results"
            class="nav-link {active["results"]}"
        >

            <span class="nav-icon">▥</span>

            <span>Results</span>

        </a>

    </nav>

<div class="sidebar-footer">

        <a
            href="/admin/logout"
            class="logout-link"
        >

            <span class="nav-icon">↪</span>

            <span>Exit Admin</span>

        </a>

    </div>

</aside>


<!-- ========================================================
     MAIN
     ======================================================== -->

<main class="main">


    <header class="topbar">

        <div class="topbar-left">

            <button
                class="mobile-menu"
                onclick="toggleSidebar()"
            >
                ☰
            </button>

            <div>

                <h1 class="page-title">
                    {safe(title)}
                </h1>

                <p class="topbar-subtitle">
                    Great Zimbabwe University Student Voting System
                </p>

            </div>

        </div>


        <div class="admin-profile">

            <div class="admin-avatar">
                AD
            </div>

            <div>

                <div class="admin-name">
                    Administrator
                </div>

                <div class="admin-role">
                    System Administrator
                </div>

            </div>

        </div>

    </header>


    <section class="content">

        {message_html}

        {content}

    </section>


</main>


<script>

function toggleSidebar() {{

    const sidebar =
        document.getElementById("sidebar");

    sidebar.classList.toggle("open");

}}


// Close mobile sidebar when a link is clicked.

document
    .querySelectorAll(".nav-link")
    .forEach(function(link){{

        link.addEventListener(
            "click",
            function(){{

                if (
                    window.innerWidth <= 800
                ){{

                    document
                        .getElementById("sidebar")
                        .classList
                        .remove("open");

                }}

            }}
        );

    }});

</script>


</body>

</html>
    """


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@router.get(
    "/admin",
    response_class=HTMLResponse
)
def admin_dashboard(
    request: Request
):

    db = get_db()

    try:

        voter_count = db.query(
            Voter
        ).count()

        election_count = db.query(
            Election
        ).count()

        candidate_count = db.query(
            Candidate
        ).count()

        ongoing_count = (
            db.query(Election)
            .filter(
                Election.status == "ongoing"
            )
            .count()
        )

        message = get_flash(request)

        content = f"""

        <div class="page-heading">

            <div>

                <h2>
                    Dashboard Overview
                </h2>

                <p>
                    Monitor and manage the GZU student
                    voting system.
                </p>

            </div>

        </div>


        <div class="stats-grid">

            <div class="stat-card">

                <div class="stat-top">

                    <div class="stat-icon">
                        ♙
                    </div>

                </div>

                <h3>
                    Total Voters
                </h3>

                <strong>
                    {voter_count}
                </strong>

            </div>


            <div class="stat-card">

                <div class="stat-top">

                    <div class="stat-icon">
                        ▣
                    </div>

                </div>

                <h3>
                    Total Elections
                </h3>

                <strong>
                    {election_count}
                </strong>

            </div>


            <div class="stat-card">

                <div class="stat-top">

                    <div class="stat-icon">
                        ♟
                    </div>

                </div>

                <h3>
                    Total Candidates
                </h3>

                <strong>
                    {candidate_count}
                </strong>

            </div>


            <div class="stat-card">

                <div class="stat-top">

                    <div class="stat-icon">
                        ●
                    </div>

                </div>

                <h3>
                    Ongoing Elections
                </h3>

                <strong>
                    {ongoing_count}
                </strong>

            </div>

        </div>


        <div class="card">

            <div class="card-header">

                <h3>
                    Quick Actions
                </h3>

            </div>


            <div class="card-body">

                <div class="quick-grid">

                    <div class="quick-card">

                        <div class="quick-icon">
                            ♙
                        </div>

                        <h3>
                            Voters
                        </h3>

                        <p>
                            Create and manage eligible
                            student voters.
                        </p>

                        <a
                            class="button"
                            href="/admin/voters"
                        >
                            Manage Voters
                        </a>

                    </div>


                    <div class="quick-card">

                        <div class="quick-icon">
                            ▣
                        </div>

                        <h3>
                            Elections
                        </h3>

                        <p>
                            Create, start and manage
                            student elections.
                        </p>

                        <a
                            class="button"
                            href="/admin/elections"
                        >
                            Manage Elections
                        </a>

                    </div>


                    <div class="quick-card">

                        <div class="quick-icon">
                            ♟
                        </div>

                        <h3>
                            Candidates
                        </h3>

                        <p>
                            Add and manage election
                            candidates.
                        </p>

                        <a
                            class="button"
                            href="/admin/candidates"
                        >
                            Manage Candidates
                        </a>

                    </div>


                    <div class="quick-card">

                        <div class="quick-icon">
                            ▥
                        </div>

                        <h3>
                            Results
                        </h3>

                        <p>
                            View blockchain-based
                            election results.
                        </p>

                        <a
                            class="button"
                            href="/admin/results"
                        >
                            View Results
                        </a>

                    </div>

                </div>

            </div>

        </div>


        <div class="card">

            <div class="card-header">

                <h3>
                    System Information
                </h3>

            </div>

            <div class="card-body">

                <p>
                    <strong>Platform:</strong>
                    GZU Student Voting System
                </p>

                <p>
                    <strong>Voting technology:</strong>
                    Blockchain-based voting
                </p>

                <p>
                    <strong>Backend:</strong>
                    FastAPI
                </p>

                <p>
                    <strong>Database:</strong>
                    SQLite
                </p>

            </div>

        </div>

        """

        return HTMLResponse(
            page_template(
                "Dashboard",
                content,
                message,
                "dashboard"
            )
        )

    finally:
        db.close()


# ============================================================
# VOTER MANAGEMENT
# ============================================================

@router.get(
    "/admin/voters",
    response_class=HTMLResponse
)
def voter_management(
    request: Request
):

    db = get_db()

    try:

        voters = (
            db.query(Voter)
            .order_by(Voter.id.desc())
            .all()
        )

        message = get_flash(request)

        rows = ""

        for voter in voters:

            rows += f"""
            <tr>

                <td>
                    {voter.id}
                </td>

                <td>
                    <strong>
                        {safe(voter.student_id)}
                    </strong>
                </td>

                <td>
                    {safe(voter.email)}
                </td>
                <td>
                    <div class="action-buttons">
                        <a class="button" href="/admin/voters/{voter.id}/edit">Edit</a>
                        <form method="post" action="/admin/voters/{voter.id}/delete"
                              onsubmit="return confirm('Delete this student account? Their voting records will also be removed.');">
                            {csrf_input(request)}
                            <button type="submit" class="button button-danger">Delete</button>
                        </form>
                    </div>
                </td>

            </tr>
            """

        content = f"""

        <div class="page-heading">

            <div>

                <h2>
                    Voter Management
                </h2>

                <p>
                    Manage students who can participate
                    in elections.
                </p>

            </div>


            <a
                class="button"
                href="/admin/voters/create"
            >
                + Create Voter
            </a>

        </div>


        <div class="card">

            <div class="card-header">

                <h3>
                    Registered Voters
                </h3>

                <span>
                    {len(voters)} voters
                </span>

            </div>


            <div class="card-body">

                <div class="table-wrapper">

                    <table>

                        <thead>

                            <tr>

                                <th>ID</th>
                                <th>Student ID</th>
                                <th>Email</th>
                                <th>Actions</th>

                            </tr>

                        </thead>


                        <tbody>

                            {
                                rows
                                if rows
                                else
                                '''
                                <tr>
                                    <td colspan="4">
                                        <div class="empty-state">
                                            <div class="empty-icon">♙</div>
                                            No voters available.
                                        </div>
                                    </td>
                                </tr>
                                '''
                            }

                        </tbody>

                    </table>

                </div>

            </div>

        </div>

        """

        return HTMLResponse(
            page_template(
                "Voters",
                content,
                message,
                "voters"
            )
        )

    finally:
        db.close()


# ============================================================
# CREATE VOTER GET
# ============================================================

@router.get(
    "/admin/voters/create",
    response_class=HTMLResponse
)
def create_voter_page(
    request: Request
):

    message = get_flash(request)

    content = """

    <div class="page-heading">

        <div>

            <h2>
                Create Voter
            </h2>

            <p>
                Add a student to the voting system.
            </p>

        </div>

    </div>


    <div class="form-card">

        <h2>
            Voter Information
        </h2>

        <p class="form-description">
            Enter the student's details below.
        </p>


        <form
            method="post"
            action="/admin/voters/create"
        >
            {csrf_input(request)}
            <label>
                Student ID
            </label>

            <input
                type="text"
                name="student_id"
                placeholder="e.g. M250000"
                required
            >


            <label>
                Email
            </label>

            <input
                type="email"
                name="email"
                placeholder="student@example.com"
                required
            >


            <label>
                Password
            </label>

            <input
                type="password"
                name="password"
                required
            >


            <div class="form-actions">

                <button
                    type="submit"
                    class="button"
                >
                    Create Voter
                </button>

                <a
                    href="/admin/voters"
                    class="button button-light"
                >
                    Cancel
                </a>

            </div>

        </form>

    </div>

    """

    return HTMLResponse(
        page_template(
            "Create Voter",
            content,
            message,
            "voters"
        )
    )


# ============================================================
# CREATE VOTER POST
# ============================================================

@router.post(
    "/admin/voters/create"
)
def create_voter(

    request: Request,

    student_id: str = Form(...),

    email: str = Form(...),

    password: str = Form(...)

):

    db = get_db()

    try:

        existing_student = (
            db.query(Voter)
            .filter(
                Voter.student_id == student_id
            )
            .first()
        )

        if existing_student:

            set_flash(
                request,
                f"Voter {student_id} already exists."
            )

            return RedirectResponse(
                "/admin/voters",
                status_code=303
            )

        existing_email = (
            db.query(Voter)
            .filter(
                Voter.email == email
            )
            .first()
        )

        if existing_email:

            set_flash(
                request,
                f"Email {email} is already registered."
            )

            return RedirectResponse(
                "/admin/voters",
                status_code=303
            )

        import bcrypt

        if len(password.encode("utf-8")) > 72:

            set_flash(
                request,
                "Password is too long. "
                "Please use a password of 72 bytes or less."
            )

            return RedirectResponse(
                "/admin/voters/create",
                status_code=303
            )

        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        voter = Voter(
            student_id=student_id,
            email=email,
            password=hashed_password
        )

        db.add(voter)

        db.commit()

        set_flash(
            request,
            f"Voter {student_id} was created successfully."
        )

        return RedirectResponse(
            "/admin/voters",
            status_code=303
        )

    except Exception as e:

        db.rollback()

        set_flash(
            request,
            f"Unable to create voter: {str(e)}"
        )

        return RedirectResponse(
            "/admin/voters",
            status_code=303
        )

    finally:

        db.close()


# ============================================================
# ELECTION MANAGEMENT
# ============================================================

@router.get(
    "/admin/elections",
    response_class=HTMLResponse
)
def election_management(

    request: Request,

    search: str = "",

    status_filter: str = "all"

):

    db = get_db()

    try:

        query = db.query(Election)

        # Archived elections are hidden from the normal management list,
        # but remain available through the Archived filter for audit/history.
        if status_filter == "archived":
            query = query.filter(Election.is_deleted == True)
        else:
            query = query.filter(Election.is_deleted == False)

        if search.strip():

            query = query.filter(
                Election.title.ilike(
                    f"%{search.strip()}%"
                )
            )

        if status_filter in [
            "upcoming",
            "ongoing",
            "closed",
            "cancelled"
        ]:

            query = query.filter(
                Election.status == status_filter
            )

        elections = (
            query
            .order_by(Election.id.desc())
            .all()
        )

        message = get_flash(request)

        election_cards = ""

        for election in elections:

            status = (
                election.status
                or "unknown"
            )

            if status == "upcoming":
                status_class = "status-upcoming"

            elif status == "ongoing":
                status_class = "status-ongoing"

            elif status == "closed":
                status_class = "status-closed"

            elif status == "cancelled":
                status_class = "status-closed"

            else:
                status_class = "status-unknown"

            election_cards += f"""

            <div class="election-card">

                <div class="election-header">

                    <div>

                        <h3>
                            {safe(election.title)}
                        </h3>

                        <div class="election-meta">
                            Election ID: {election.id}
                        </div>

                    </div>


                    <span
                        class="status {status_class}"
                    >
                        {safe(status).upper()}
                    </span>

                </div>


                <div class="election-description">

                    {safe(
                        election.description
                        or
                        "No description provided."
                    )}

                </div>


                <div class="action-row">

                    <a
                        class="button"
                        href="/admin/elections/{election.id}"
                    >
                        Manage Election
                    </a>
                    <a class="button" href="/admin/elections/{election.id}/edit">Edit Settings</a>
                    {f'<form method="post" action="/admin/elections/{election.id}/cancel" onsubmit="return confirm(\'Cancel this election? Voting will stop and its history will be retained.\');">{csrf_input(request)}<button type="submit" class="button button-danger">Cancel Election</button></form>' if status in ("upcoming", "ongoing") else ""}
                    {f'<form method="post" action="/admin/elections/{election.id}/delete" onsubmit="return confirm(\'Archive this election? Its history and blockchain records will be retained.\');">{csrf_input(request)}<button type="submit" class="button button-danger">Archive Election</button></form>' if not election.is_deleted else '<span class="status status-closed">ARCHIVED</span>'}

                </div>

            </div>

            """

        content = f"""

        <div class="page-heading">

            <div>

                <h2>
                    Election Management
                </h2>

                <p>
                    Create and manage GZU student elections.
                </p>

            </div>


            <a
                class="button"
                href="/admin/elections/create"
            >
                + Create Election
            </a>

        </div>


        <div class="search-panel">

            <form
                method="get"
                action="/admin/elections"
            >

                <div class="search-row">

                    <input
                        type="text"
                        name="search"
                        value="{safe(search)}"
                        placeholder="Search election name..."
                    >


                    <select
                        name="status_filter"
                    >

                        <option
                            value="all"
                            {"selected" if status_filter == "all" else ""}
                        >
                            All Elections
                        </option>


                        <option
                            value="upcoming"
                            {"selected" if status_filter == "upcoming" else ""}
                        >
                            Upcoming
                        </option>


                        <option
                            value="ongoing"
                            {"selected" if status_filter == "ongoing" else ""}
                        >
                            Ongoing
                        </option>


                        <option
                            value="closed"
                            {"selected" if status_filter == "closed" else ""}
                        >
                            Closed
                        </option>

                        <option value="cancelled" {"selected" if status_filter == "cancelled" else ""}>Cancelled</option>
                        <option value="archived" {"selected" if status_filter == "archived" else ""}>Archived</option>

                    </select>


                    <button
                        type="submit"
                        class="button"
                    >
                        Search
                    </button>

                </div>

            </form>

        </div>


        {
            election_cards
            if election_cards
            else
            '''
            <div class="card">

                <div class="empty-state">

                    <div class="empty-icon">
                        ▣
                    </div>

                    No elections found.

                </div>

            </div>
            '''
        }

        """

        return HTMLResponse(
            page_template(
                "Elections",
                content,
                message,
                "elections"
            )
        )

    finally:

        db.close()


# ============================================================
# CREATE ELECTION GET
# ============================================================

@router.get(
    "/admin/elections/create",
    response_class=HTMLResponse
)
def create_election_page(
    request: Request
):

    message = get_flash(request)

    content = """

    <div class="page-heading">

        <div>

            <h2>
                Create Election
            </h2>

            <p>
                Create a new student election.
            </p>

        </div>

    </div>


    <div class="form-card">

        <h2>
            Election Information
        </h2>

        <p class="form-description">
            The election will be created in the
            database and blockchain.
        </p>


        <form
            method="post"
            action="/admin/elections/create"
        >
            {csrf_input(request)}
            <label>
                Election Title
            </label>

            <input
                type="text"
                name="title"
                placeholder="e.g. GZU SRC Elections 2026"
                required
            >


            <label>
                Description
            </label>

            <textarea
                name="description"
                placeholder="Enter election description..."
            ></textarea>


            <div class="form-actions">

                <button
                    type="submit"
                    class="button"
                >
                    Create Election
                </button>

                <a
                    href="/admin/elections"
                    class="button button-light"
                >
                    Cancel
                </a>

            </div>

        </form>

    </div>

    """

    # Render the CSRF helper as a hidden form field, not visible text.
    content = content.replace("{csrf_input(request)}", csrf_input(request))

    return HTMLResponse(
        page_template(
            "Create Election",
            content,
            message,
            "elections"
        )
    )


# ============================================================
# CREATE ELECTION POST
# ============================================================

@router.post(
    "/admin/elections/create"
)

def create_election(
    request: Request,
    title: str = Form(...),
    description: str = Form("")
):
    db = get_db()

    try:
        title = title.strip()
        description = description.strip()

        if not title:
            set_flash(
                request,
                "Election title cannot be empty."
            )
            return RedirectResponse(
                "/admin/elections/create",
                status_code=303
            )

        from blockchain import create_election_on_blockchain

        (
            blockchain_receipt,
            blockchain_election_id
        ) = create_election_on_blockchain(title)

        blockchain_election_id = int(blockchain_election_id)

        # Check whether this blockchain ID is already mapped
        # to another SQLite election.
        existing_election = (
            db.query(Election)
            .filter(
                Election.blockchain_election_id
                == blockchain_election_id
            )
            .first()
        )

        if existing_election:
            raise Exception(
                f"Blockchain election ID {blockchain_election_id} "
                f"is already mapped to SQLite election "
                f"{existing_election.id}. The blockchain transaction "
                "has already succeeded. Do not retry creation; "
                "manual reconciliation is required."
            )

        # Let SQLite generate its own election ID.
        # Store the blockchain ID separately.
        election = Election(
            title=title,
            description=description,
            status="upcoming",
            blockchain_election_id=blockchain_election_id
        )

        db.add(election)
        db.commit()
        db.refresh(election)

        set_flash(
            request,
            f"Election '{title}' was created successfully. "
            f"SQLite ID: {election.id}; "
            f"Blockchain ID: {blockchain_election_id}."
        )

        return RedirectResponse(
            "/admin/elections",
            status_code=303
        )

    except Exception as e:
        db.rollback()

        set_flash(
            request,
            f"Unable to create election: {str(e)}"
        )

        return RedirectResponse(
            "/admin/elections",
            status_code=303
        )

    finally:
        db.close()


# ============================================================
# MANAGE SINGLE ELECTION
# ============================================================

@router.get(
    "/admin/elections/{election_id}",
    response_class=HTMLResponse
)
def manage_election(

    request: Request,

    election_id: int

):

    db = get_db()

    try:

        election = (
            db.query(Election)
            .filter(
                Election.id == election_id
            )
            .first()
        )

        if not election:

            return HTMLResponse(

                page_template(

                    "Election Not Found",

                    """
                    <div class="card">

                        <div class="empty-state">

                            <div class="empty-icon">
                                ⚠
                            </div>

                            <h2>
                                Election Not Found
                            </h2>

                            <p>
                                The requested election does not exist.
                            </p>

                            <a
                                class="button"
                                href="/admin/elections"
                            >
                                Back to Elections
                            </a>

                        </div>

                    </div>
                    """,

                    active_page="elections"

                ),

                status_code=404
            )

        candidates = (
            db.query(Candidate)
            .filter(
                Candidate.election_id == election_id
            )
            .order_by(Candidate.id)
            .all()
        )

        message = get_flash(request)

        candidate_rows = ""

        for candidate in candidates:

            candidate_rows += f"""

            <tr>

                <td>
                    {candidate.id}
                </td>

                <td>
                    <strong>
                        {safe(candidate.name)}
                    </strong>
                </td>

                <td>
                    {safe(candidate.position)}
                </td>

                <td>
                    {candidate.blockchain_candidate_id or "-"}
                </td>
                <td>
                    <div class="action-buttons">
                        <a class="button" href="/admin/candidates/{candidate.id}/edit">Edit</a>
                        <form method="post" action="/admin/candidates/{candidate.id}/delete"
                              onsubmit="return confirm('Delete this candidate? Associated votes and profile will also be removed.');">
                            {csrf_input(request)}
                            <button type="submit" class="button button-danger">Delete</button>
                        </form>
                    </div>
                </td>

            </tr>

            """

        status = (
            election.status
            or "unknown"
        )

        if status == "upcoming":
            status_class = "status-upcoming"

        elif status == "ongoing":
            status_class = "status-ongoing"

        elif status == "closed":
            status_class = "status-closed"

        else:
            status_class = "status-unknown"

        action_buttons = ""

        if status == "upcoming":

            action_buttons = f"""

            <form
                method="post"
                action="/admin/elections/{election_id}/start"
                style="display:inline;"
            >
                {csrf_input(request)}
                <button
                    type="submit"
                    class="button"
                >
                    ▶ Start Election
                </button>

            </form>

            """

        elif status == "ongoing":

            action_buttons = f"""

            <form
                method="post"
                action="/admin/elections/{election_id}/end"
                style="display:inline;"
            >
                {csrf_input(request)}
                <button
                    type="submit"
                    class="button button-danger"
                >
                    ■ End Election
                </button>

            </form>

            """

        if status in ("upcoming", "ongoing"):
            action_buttons += f"""
            <form method="post" action="/admin/elections/{election_id}/cancel" style="display:inline;"
                  onsubmit="return confirm('Cancel this election? Voting will stop and history will be retained.');">
                {csrf_input(request)}
                <button type="submit" class="button button-danger">Cancel Election</button>
            </form>
            """

        content = f"""

        <div class="page-heading">

            <div>

                <h2>
                    {safe(election.title)}
                </h2>

                <p>
                    Manage election settings and candidates.
                </p>

            </div>

        </div>


        <div class="card">

            <div class="card-header">

                <h3>
                    Election Information
                </h3>

                <span
                    class="status {status_class}"
                >
                    {safe(status).upper()}
                </span>

            </div>


            <div class="card-body">

                <p>
                    <strong>Election ID:</strong>
                    {election.id}
                </p>

                <p>
                    <strong>Description:</strong>
                    {safe(
                        election.description
                        or
                        "No description provided."
                    )}
                </p>


                <div class="action-row">

                    {action_buttons}


                    <a
                        class="button button-secondary"
                        href="/admin/candidates/create?election_id={election_id}"
                    >
                        + Add Candidate
                    </a>

                </div>

            </div>

        </div>


        <div class="card">

            <div class="card-header">

                <h3>
                    Candidates
                </h3>

                <span>
                    {len(candidates)} candidates
                </span>

            </div>


            <div class="card-body">

                <div class="table-wrapper">

                    <table>

                        <thead>

                            <tr>

                                <th>ID</th>
                                <th>Name</th>
                                <th>Position</th>
                                <th>Blockchain ID</th>
                                <th>Actions</th>

                            </tr>

                        </thead>


                        <tbody>

                            {
                                candidate_rows
                                if candidate_rows
                                else
                                '''
                                <tr>
                                    <td colspan="4">

                                        <div class="empty-state">

                                            <div class="empty-icon">
                                                ♟
                                            </div>

                                            No candidates added yet.

                                        </div>

                                    </td>
                                </tr>
                                '''
                            }

                        </tbody>

                    </table>

                </div>

            </div>

        </div>

        """

        return HTMLResponse(

            page_template(

                election.title,

                content,

                message,

                "elections"

            )

        )

    finally:

        db.close()


# ============================================================
# START ELECTION
# ============================================================

@router.post(
    "/admin/elections/{election_id}/start"
)
def start_election(

    request: Request,

    election_id: int

):

    db = get_db()

    try:

        election = (
            db.query(Election)
            .filter(
                Election.id == election_id
            )
            .first()
        )

        if not election:

            set_flash(
                request,
                "Election not found."
            )

            return RedirectResponse(
                "/admin/elections",
                status_code=303
            )

        if election.is_deleted or election.status != "upcoming":
            set_flash(
                request,
                "Only an upcoming, non-archived election can be started. "
                "Closed or cancelled elections cannot be reopened."
            )
            return RedirectResponse(
                f"/admin/elections/{election_id}",
                status_code=303
            )


        
        if election.blockchain_election_id is None:
            raise ValueError(
                "This election has no mapped blockchain ID."
            )

        blockchain_id = election.blockchain_election_id

        from blockchain import (
            get_blockchain_election_status
        )

        blockchain_status = (
            get_blockchain_election_status(
                blockchain_id
            )
        )

        if not blockchain_status["active"]:

            from blockchain import (
                start_election_on_blockchain
            )

            start_election_on_blockchain(
                blockchain_id
            )
            

        election.status = "ongoing"

        db.commit()

        set_flash(
            request,
            f"Election '{election.title}' "
            "started successfully."
        )

        return RedirectResponse(

            f"/admin/elections/{election_id}",

            status_code=303

        )

    except Exception as e:

        db.rollback()

        set_flash(
            request,
            f"Unable to start election: {str(e)}"
        )

        return RedirectResponse(

            f"/admin/elections/{election_id}",

            status_code=303

        )

    finally:

        db.close()


# ============================================================
# END ELECTION
# ============================================================

@router.post(
    "/admin/elections/{election_id}/end"
)
def end_election(

    request: Request,

    election_id: int

):

    db = get_db()

    try:

        election = (
            db.query(Election)
            .filter(
                Election.id == election_id
            )
            .first()
        )

        if not election:

            set_flash(
                request,
                "Election not found."
            )

            return RedirectResponse(
                "/admin/elections",
                status_code=303
            )

        if election.status in ("closed", "cancelled") or election.is_deleted:
            set_flash(
                request,
                "This election is already closed, cancelled, or archived."
            )
            return RedirectResponse(
                f"/admin/elections/{election_id}",
                status_code=303
            )

        
        if election.blockchain_election_id is None:
            raise ValueError(
                "This election has no mapped blockchain ID."
            )

        blockchain_id = election.blockchain_election_id

        from blockchain import (
            end_election_on_blockchain,
            get_blockchain_election_status
        )

        blockchain_status = (
            get_blockchain_election_status(
                blockchain_id
            )
        )

        if blockchain_status["active"]:

            end_election_on_blockchain(
                blockchain_id
            )

    
        election.status = "closed"

        db.commit()

        set_flash(
            request,
            f"Election '{election.title}' "
            "ended successfully."
        )

        return RedirectResponse(

            f"/admin/elections/{election_id}",

            status_code=303

        )

    except Exception as e:

        db.rollback()

        set_flash(
            request,
            f"Unable to end election: {str(e)}"
        )

        return RedirectResponse(

            f"/admin/elections/{election_id}",

            status_code=303

        )

    finally:

        db.close()


@router.post("/admin/elections/{election_id}/cancel")
def cancel_election(request: Request, election_id: int, admin: str = Depends(require_admin)):
    """Cancel an election without deleting its database or blockchain history."""
    db = get_db()
    try:
        election = db.query(Election).filter(
            Election.id == election_id,
            Election.is_deleted == False
        ).first()
        if not election:
            set_flash(request, "Election was not found or is already archived.")
            return RedirectResponse("/admin/elections", status_code=303)
        if election.status in ("closed", "cancelled"):
            set_flash(request, f"Election '{election.title}' is already {election.status}.")
            return RedirectResponse(f"/admin/elections/{election_id}", status_code=303)

        
        # Cancellation is recorded separately on-chain and in SQLite.
        if election.blockchain_election_id is None:
            raise ValueError(
                "This election has no mapped blockchain ID."
            )

        blockchain_id = election.blockchain_election_id

        from blockchain import cancel_election_on_blockchain
        cancel_election_on_blockchain(blockchain_id)


        election.status = "cancelled"
        db.commit()
        set_flash(request, f"Election '{election.title}' cancelled. Voting stopped; history retained.")
        return RedirectResponse("/admin/elections", status_code=303)
    except Exception as exc:
        db.rollback()
        set_flash(request, f"Unable to cancel election: {type(exc).__name__}: {exc}")
        return RedirectResponse(f"/admin/elections/{election_id}", status_code=303)
    finally:
        db.close()


# ============================================================
# CANDIDATE MANAGEMENT
# ============================================================

@router.get(
    "/admin/candidates",
    response_class=HTMLResponse
)
def candidate_management(
    request: Request
):

    db = get_db()

    try:

        candidates = (
            db.query(Candidate)
            .order_by(Candidate.id.desc())
            .all()
        )

        elections = (
            db.query(Election)
            .all()
        )

        message = get_flash(request)

        election_lookup = {
            election.id:
            election.title
            for election in elections
        }

        rows = ""

        for candidate in candidates:

            election_title = (
                election_lookup.get(
                    candidate.election_id,
                    "Unknown"
                )
            )

            rows += f"""

            <tr>

                <td>
                    {candidate.id}
                </td>

                <td>
                    <strong>
                        {safe(candidate.name)}
                    </strong>
                </td>

                <td>
                    {safe(candidate.position)}
                </td>

                <td>
                    {safe(election_title)}
                </td>

                <td>
                    {candidate.blockchain_candidate_id or "-"}
                </td>
                <td><a class="button" href="/admin/candidates/{candidate.id}/edit">Edit</a></td>

            </tr>

            """

        content = f"""

        <div class="page-heading">

            <div>

                <h2>
                    Candidate Management
                </h2>

                <p>
                    Manage candidates for student elections.
                </p>

            </div>


            <a
                class="button"
                href="/admin/candidates/create"
            >
                + Add Candidate
            </a>

        </div>


        <div class="card">

            <div class="card-header">

                <h3>
                    All Candidates
                </h3>

                <span>
                    {len(candidates)} candidates
                </span>

            </div>


            <div class="card-body">

                <div class="table-wrapper">

                    <table>

                        <thead>

                            <tr>

                                <th>ID</th>
                                <th>Name</th>
                                <th>Position</th>
                                <th>Election</th>
                                <th>Blockchain ID</th>
                                <th>Actions</th>

                            </tr>

                        </thead>


                        <tbody>

                            {
                                rows
                                if rows
                                else
                                '''
                                <tr>
                                    <td colspan="6">

                                        <div class="empty-state">

                                            <div class="empty-icon">
                                                ♟
                                            </div>

                                            No candidates available.

                                        </div>

                                    </td>
                                </tr>
                                '''
                            }

                        </tbody>

                    </table>

                </div>

            </div>

        </div>

        """

        return HTMLResponse(

            page_template(

                "Candidates",

                content,

                message,

                "candidates"

            )

        )

    finally:

        db.close()


# ============================================================
# CREATE CANDIDATE GET
# ============================================================

@router.get(
    "/admin/candidates/create",
    response_class=HTMLResponse
)
def create_candidate_page(

    request: Request,

    election_id: int = None

):

    db = get_db()

    try:

        elections = (
            db.query(Election)
            .order_by(Election.id.desc())
            .all()
        )

        message = get_flash(request)

        options = ""

        for election in elections:

            selected = (
                "selected"
                if election_id == election.id
                else ""
            )

            options += f"""

            <option
                value="{election.id}"
                {selected}
            >
                {safe(election.title)}
            </option>

            """

        content = f"""

        <div class="page-heading">

            <div>

                <h2>
                    Add Candidate
                </h2>

                <p>
                    Add a candidate to an election.
                </p>

            </div>

        </div>


        <div class="form-card">

            <h2>
                Candidate Information
            </h2>

            <p class="form-description">
                The candidate will be linked to the
                blockchain election.
            </p>


            <form
                method="post"
                action="/admin/candidates/create"
            >
                {csrf_input(request)}
                <label>
                    Election
                </label>


                <select
                    name="election_id"
                    required
                >

                    <option value="">
                        Select election
                    </option>

                    {options}

                </select>


                <label>
                    Candidate Name
                </label>


                <input
                    type="text"
                    name="name"
                    placeholder="Candidate name"
                    required
                >


                <label>
                    Position
                </label>


                <input
                    type="text"
                    name="position"
                    placeholder="e.g. President"
                    required
                >


                <div class="form-actions">

                    <button
                        type="submit"
                        class="button"
                    >
                        Add Candidate
                    </button>

                    <a
                        href="/admin/candidates"
                        class="button button-light"
                    >
                        Cancel
                    </a>

                </div>

            </form>

        </div>

        """

        return HTMLResponse(

            page_template(

                "Add Candidate",

                content,

                message,

                "candidates"

            )

        )

    finally:

        db.close()


# ============================================================
# CREATE CANDIDATE POST
# ============================================================

@router.post(
    "/admin/candidates/create"
)

def create_candidate(
    request: Request,
    election_id: int = Form(...),
    name: str = Form(...),
    position: str = Form(...)
):
    db = get_db()

    try:
        name = name.strip()
        position = position.strip()

        election = (
            db.query(Election)
            .filter(Election.id == election_id)
            .first()
        )

        if not election:
            set_flash(
                request,
                "Selected election does not exist."
            )
            return RedirectResponse(
                "/admin/candidates",
                status_code=303
            )

        if election.status == "closed":
            set_flash(
                request,
                "Cannot add a candidate to a closed election."
            )
            return RedirectResponse(
                f"/admin/elections/{election_id}",
                status_code=303
            )

        if not name:
            set_flash(
                request,
                "Candidate name cannot be empty."
            )
            return RedirectResponse(
                f"/admin/elections/{election_id}",
                status_code=303
            )

        if not position:
            set_flash(
                request,
                "Candidate position cannot be empty."
            )
            return RedirectResponse(
                f"/admin/elections/{election_id}",
                status_code=303
            )

        if election.blockchain_election_id is None:
            raise ValueError(
                "This election has no mapped blockchain ID."
            )

        blockchain_id = election.blockchain_election_id

        from blockchain import (
            add_candidate_to_blockchain,
            get_blockchain_candidate_count,
            get_blockchain_candidate
        )

        existing_candidate = (
            db.query(Candidate)
            .filter(
                Candidate.election_id == election_id,
                Candidate.name == name,
                Candidate.position == position
            )
            .first()
        )

        if existing_candidate:
            set_flash(
                request,
                f"Candidate '{name}' already exists "
                "for this position."
            )
            return RedirectResponse(
                f"/admin/elections/{election_id}",
                status_code=303
            )

        blockchain_candidate_id = None

        blockchain_candidate_count = (
            get_blockchain_candidate_count(blockchain_id)
        )

        for candidate_id in range(
            1,
            blockchain_candidate_count + 1
        ):
            blockchain_candidate = get_blockchain_candidate(
                blockchain_id,
                candidate_id
            )

            blockchain_name = blockchain_candidate["name"]
            blockchain_position = blockchain_candidate["position"]

            if (
                blockchain_name.strip().lower() == name.lower()
                and blockchain_position.strip().lower() == position.lower()
            ):
                blockchain_candidate_id = candidate_id
                break

        if blockchain_candidate_id is None:
            (
                blockchain_receipt,
                blockchain_candidate_id
            ) = add_candidate_to_blockchain(
                blockchain_id,
                name,
                position
            )

        candidate = Candidate(
            election_id=election_id,
            name=name,
            position=position,
            blockchain_candidate_id=int(blockchain_candidate_id)
        )

        db.add(candidate)
        db.commit()

        set_flash(
            request,
            f"Candidate '{name}' was added successfully. "
            f"Blockchain candidate ID: {blockchain_candidate_id}."
        )

        return RedirectResponse(
            f"/admin/elections/{election_id}",
            status_code=303
        )

    except Exception as e:
        db.rollback()

        set_flash(
            request,
            f"Unable to add candidate: {str(e)}"
        )

        return RedirectResponse(
            f"/admin/elections/{election_id}",
            status_code=303
        )

    finally:
        db.close()


# ============================================================
# RESULTS
# ============================================================



# ============================================================
# RESULTS
# ============================================================

@router.get(
    "/admin/results",
    response_class=HTMLResponse
)
def admin_results(
    request: Request
):

    db = get_db()

    try:

        elections = (
            db.query(Election)
            .order_by(Election.id.desc())
            .all()
        )

        content_parts = [

            """
            <div class="page-heading">

                <div>

                    <h2>
                        Election Results
                    </h2>

                    <p>
                        Results are retrieved directly
                        from the blockchain.
                    </p>

                </div>

            </div>
            """

        ]

        from blockchain import (
            get_candidate_vote_count
        )

        
        for election in elections:

            if election.blockchain_election_id is None:
                content_parts.append(
                    f"""
                    <div class="card">
                        <p>Blockchain mapping is missing for
                        {safe(election.title)}.</p>
                    </div>
                    """
                )
                continue

            blockchain_id = election.blockchain_election_id

            candidates = (

                db.query(Candidate)
                .filter(
                    Candidate.election_id
                    == election.id
                )
                .order_by(Candidate.id)
                .all()
            )

            if not candidates:
                continue

            status = (
                election.status
                or "unknown"
            )

            if status == "upcoming":
                status_class = "status-upcoming"

            elif status == "ongoing":
                status_class = "status-ongoing"

            elif status == "closed":
                status_class = "status-closed"

            else:
                status_class = "status-unknown"

            content_parts.append(

                f"""

                <div class="card">

                    <div class="card-header">

                        <h3>
                            {safe(election.title)}
                        </h3>

                        <span
                            class="status {status_class}"
                        >
                            {safe(status).upper()}
                        </span>

                    </div>

                    <div class="card-body">

                """

            )

            positions = sorted(

                set(

                    candidate.position

                    for candidate in candidates

                )

            )

            for position in positions:

                content_parts.append(

                    f"""

                    <h3
                        style="
                            margin:
                                5px 0 12px;
                            font-size:18px;
                        "
                    >
                        {safe(position)}
                    </h3>


                    <div class="table-wrapper">

                        <table>

                            <thead>

                                <tr>

                                    <th>
                                        Candidate
                                    </th>

                                    <th>
                                        Votes
                                    </th>

                                </tr>

                            </thead>


                            <tbody>

                    """

                )

                position_candidates = [

                    candidate

                    for candidate in candidates

                    if candidate.position == position

                ]

                for candidate in position_candidates:

                    if not candidate.blockchain_candidate_id:

                        votes = 0

                    else:
                        
                        votes = (
                            get_candidate_vote_count(
                                blockchain_id,
                                candidate.blockchain_candidate_id
                            )
                        )

                    content_parts.append(

                        f"""

                        <tr>

                            <td>
                                <strong>
                                    {safe(candidate.name)}
                                </strong>
                            </td>

                            <td>
                                {votes}
                            </td>

                        </tr>

                        """

                    )

                content_parts.append(

                    """

                            </tbody>

                        </table>

                    </div>

                    <br>

                    """

                )

            content_parts.append(
                """
                    </div>
                </div>
                """
            )

        if len(content_parts) == 1:

            content_parts.append(

                """

                <div class="card">

                    <div class="empty-state">

                        <div class="empty-icon">
                            ▥
                        </div>

                        No election results available.

                    </div>

                </div>

                """

            )

        content = "".join(
            content_parts
        )

        message = get_flash(
            request
        )

        return HTMLResponse(

            page_template(

                "Results",

                content,

                message,

                "results"

            )

        )

    except Exception as blockchain_error:

        content = f"""

        <div class="card">

            <div class="empty-state">

                <div class="empty-icon">
                    ⚠
                </div>

                <h2>
                    Blockchain Error
                </h2>

                <p>
                    {safe(blockchain_error)}
                </p>

            </div>

        </div>

        """

        return HTMLResponse(

            page_template(

                "Results",

                content,

                active_page="results"

            )

        )

    finally:

        db.close()


# ============================================================
# CANDIDATE NOMINATION REVIEW
# ============================================================

@router.get("/admin/nominations", response_class=HTMLResponse)
def admin_nominations(
    request: Request,
    status: str = "pending",
    _admin: str = Depends(require_admin),
):
    allowed = {"pending", "approved", "rejected", "corrections_requested", "all"}
    if status not in allowed:
        status = "pending"

    # Token protects review forms when browsers omit Origin and Referer.
    csrf_token = secrets.token_urlsafe(32)
    request.session["admin_review_csrf"] = csrf_token

    db = get_db()
    try:
        query = db.query(CandidateNomination)
        if status != "all":
            query = query.filter(CandidateNomination.status == status)
        nominations = query.order_by(CandidateNomination.id.desc()).all()
        message = get_flash(request)
        options = "".join(
            f'<option value="{key}"{" selected" if key == status else ""}>{label}</option>'
            for key, label in [
                ("pending", "Pending"), ("approved", "Approved"),
                ("rejected", "Rejected"), ("corrections_requested", "Corrections requested"),
                ("all", "All nominations")
            ]
        )
        if not nominations:
            rows = '<div class="card" style="padding:24px 28px;"><p style="margin:0;line-height:1.6;">No nominations found for this status.</p></div>'
        else:
            cards = []
            for item in nominations:
                photo = f'/candidate-photos/{safe(item.photo_path)}' if item.photo_path else ''
                photo_html = f'<img src="{photo}" alt="Candidate photo" style="width:120px;height:140px;object-fit:cover;border-radius:10px;">' if photo else '<div style="width:120px;height:140px;background:#eee;border-radius:10px;display:flex;align-items:center;justify-content:center;">No photo</div>'
                feedback = safe(item.admin_feedback)
                created = safe(item.created_at)
                status_label = safe(str(item.status or '').replace('_', ' ').title())
                if item.status == 'pending':
                    actions = f'''
                    <form method="post" action="/admin/nominations/{item.id}/review" style="display:grid;gap:10px;margin-top:14px;">
                      {csrf_input(request)}
                      <label>Feedback (optional)<textarea name="feedback" rows="2" style="width:100%;padding:10px;border:1px solid #d1d5db;border-radius:8px;"></textarea></label>
                      <div style="display:flex;gap:8px;flex-wrap:wrap;">
                        <button class="button" type="submit" name="decision" value="approve">Approve</button>
                        <button class="button button-secondary" type="submit" name="decision" value="request_corrections">Request corrections</button>
                        <button class="button button-danger" type="submit" name="decision" value="reject">Reject</button>
                      </div>
                    </form>'''
                else:
                    actions = '<p style="color:#64748b;">This nomination has already been reviewed.</p>'
                cards.append(f'''
                <article class="card" style="margin-bottom:18px;">
                  <div style="display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap;">
                    <div>{photo_html}</div>
                    <div style="flex:1;min-width:240px;">
                      <h3 style="margin:0 0 8px;">{safe(item.full_name)} — {safe(item.position)}</h3>
                      <p><strong>Status:</strong> {status_label} &nbsp; <strong>Nomination ID:</strong> {item.id}</p>
                      <p><strong>Student ID:</strong> {safe(item.student_id)} &nbsp; <strong>Election ID:</strong> {item.election_id}</p>
                      <p><strong>Faculty:</strong> {safe(item.faculty)} &nbsp; <strong>Department:</strong> {safe(item.department)}</p>
                      <p><strong>Programme:</strong> {safe(item.programme)} &nbsp; <strong>Year:</strong> {safe(item.year_of_study)}</p>
                      <p><strong>Experience:</strong><br>{safe(item.experience) or 'Not provided'}</p>
                      <p><strong>Manifesto:</strong><br>{safe(item.manifesto)}</p>
                      <p><strong>Submitted:</strong> {created}</p>
                      {f'<p><strong>Admin feedback:</strong><br>{feedback}</p>' if feedback else ''}
                      {actions}
                    </div>
                  </div>
                </article>''')
            rows = ''.join(cards)
        content = f'''
        <div class="page-heading nominations-page-heading">
          <div>
            <h1>Candidate Nominations</h1>
            <p>Review student nomination details and candidate photos.</p>
          </div>
        </div>
        <div class="card" style="margin-bottom:20px;padding:24px 28px;">
          <form method="get" action="/admin/nominations" style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
            <label for="status">Filter by status</label>
            <select id="status" name="status" style="padding:10px;border:1px solid #d1d5db;border-radius:8px;">{options}</select>
            <button class="button" type="submit">Filter</button>
          </form>
          <p style="margin:18px 0 0;line-height:1.6;">Total shown: <strong>{len(nominations)}</strong></p>
        </div>
        {rows}
        '''
        return HTMLResponse(page_template("Candidate Nominations", content, message, "nominations"))
    finally:
        db.close()


@router.get("/admin/nominations/{nomination_id}/review", response_class=HTMLResponse)
def admin_review_nomination_get(
    nomination_id: int,
    request: Request,
    _admin: str = Depends(require_admin),
):
    """
    A review decision must be submitted with POST. If a browser or an old
    link opens the review URL with GET, send the administrator back to the
    nominations list instead of returning 405. No nomination status is changed.
    """
    db = get_db()
    try:
        item = (
            db.query(CandidateNomination)
            .filter(CandidateNomination.id == nomination_id)
            .first()
        )
        if item is None:
            set_flash(request, "Nomination not found.")
        else:
            set_flash(
                request,
                "To review a nomination, use Approve, Request corrections, "
                "or Reject on the Candidate Nominations page."
            )
        return RedirectResponse("/admin/nominations", status_code=303)
    finally:
        db.close()


@router.post("/admin/nominations/{nomination_id}/review")
def admin_review_nomination_page(
    nomination_id: int,
    request: Request,
    decision: str = Form(...),
    feedback: str = Form(""),
    _admin: str = Depends(require_admin),
):
    if decision not in {"approve", "reject", "request_corrections"}:
        set_flash(request, "Invalid review decision.")
        return RedirectResponse("/admin/nominations", status_code=303)

    db = get_db()
    try:
        item = db.query(CandidateNomination).filter(CandidateNomination.id == nomination_id).first()
        if not item:
            set_flash(request, "Nomination not found.")
            return RedirectResponse("/admin/nominations", status_code=303)
        if item.status != "pending":
            set_flash(request, "Only pending nominations can be reviewed.")
            return RedirectResponse("/admin/nominations?status=all", status_code=303)

        
        if decision == "approve":
            election = (
                db.query(Election)
                .filter(Election.id == item.election_id)
                .first()
            )

            if not election or election.status != "upcoming":
                set_flash(
                    request,
                    "This candidate cannot be approved because the election is not upcoming."
                )
                return RedirectResponse(
                    "/admin/nominations",
                    status_code=303
                )

            if election.blockchain_election_id is None:
                set_flash(
                    request,
                    "Candidate approval failed: this election has no blockchain mapping."
                )
                return RedirectResponse(
                    "/admin/nominations",
                    status_code=303
                )

            blockchain_id = election.blockchain_election_id

            try:
                _receipt, chain_id = add_candidate_to_blockchain(
                    blockchain_id,
                    item.full_name,
                    item.position
                )
            except Exception as exc:
                db.rollback()
                set_flash(
                    request,
                    f"Blockchain registration failed ({type(exc).__name__}). Check the blockchain node and try again."
                )
                return RedirectResponse(
                    "/admin/nominations",
                    status_code=303
                )

            candidate = Candidate(
                election_id=item.election_id,
                name=item.full_name,
                position=item.position,
                blockchain_candidate_id=int(chain_id),
            )
            db.add(candidate)
            db.flush()
            db.add(CandidateProfile(
                candidate_id=candidate.id,
                photo_path=item.photo_path,
                faculty=item.faculty,
                department=item.department,
                programme=item.programme,
                year_of_study=item.year_of_study,
                manifesto=item.manifesto,
                experience=item.experience,
            ))
            item.candidate_id = candidate.id
            item.status = "approved"
            message = "Nomination approved and candidate registered."
        elif decision == "reject":
            item.status = "rejected"
            message = "Nomination rejected."
        else:
            item.status = "corrections_requested"
            message = "Corrections requested from the student."

        item.admin_feedback = feedback.strip() or None
        from datetime import datetime, timezone
        item.reviewed_at = datetime.now(timezone.utc).isoformat()
        db.commit()
        set_flash(request, message)
        return RedirectResponse("/admin/nominations", status_code=303)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()



# ============================================================
# ADMIN DELETE ACTIONS
# ============================================================

@router.post("/admin/voters/{voter_id}/delete")
def delete_voter(
    request: Request,
    voter_id: int,
    admin: str = Depends(require_admin)
):
    db = get_db()

    try:
        voter = (
            db.query(Voter)
            .filter(Voter.id == voter_id)
            .first()
        )

        if not voter:
            set_flash(request, "Student account was not found.")
            return RedirectResponse("/admin/voters", status_code=303)

        existing_record = (
            db.query(VotingRecord)
            .filter(
                VotingRecord.student_id == voter.student_id
            )
            .first()
        )

        if existing_record:
            set_flash(
                request,
                "This student has voting history. "
                "The account cannot be deleted because historical "
                "voting records must be preserved."
            )
            return RedirectResponse("/admin/voters", status_code=303)

        student_id = voter.student_id
        db.delete(voter)
        db.commit()

        set_flash(request, f"Student account {student_id} was deleted.")
        return RedirectResponse("/admin/voters", status_code=303)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


@router.post("/admin/candidates/{candidate_id}/delete")
def delete_candidate(
    request: Request,
    candidate_id: int,
    admin: str = Depends(require_admin)
):
    db = get_db()

    try:
        candidate = (
            db.query(Candidate)
            .filter(Candidate.id == candidate_id)
            .first()
        )

        if not candidate:
            set_flash(request, "Candidate was not found.")
            return RedirectResponse("/admin/candidates", status_code=303)

        election = (
            db.query(Election)
            .filter(Election.id == candidate.election_id)
            .first()
        )

        if (
            election
            and election.blockchain_election_id is not None
        ):
            set_flash(
                request,
                "This candidate belongs to a blockchain-linked "
                "election. Deletion is disabled to preserve history."
            )
            return RedirectResponse("/admin/candidates", status_code=303)

        existing_vote = (
            db.query(Vote)
            .filter(Vote.candidate_id == candidate_id)
            .first()
        )

        if existing_vote:
            set_flash(
                request,
                "This candidate has voting records and cannot be deleted."
            )
            return RedirectResponse("/admin/candidates", status_code=303)

        existing_nomination = (
            db.query(CandidateNomination)
            .filter(
                CandidateNomination.candidate_id == candidate_id
            )
            .first()
        )

        if existing_nomination:
            set_flash(
                request,
                "This candidate is linked to nomination history "
                "and cannot be deleted."
            )
            return RedirectResponse("/admin/candidates", status_code=303)

        db.query(CandidateProfile).filter(
            CandidateProfile.candidate_id == candidate_id
        ).delete(synchronize_session=False)

        db.delete(candidate)
        db.commit()

        set_flash(request, "Candidate deleted successfully.")
        return RedirectResponse("/admin/candidates", status_code=303)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


@router.post("/admin/elections/{election_id}/delete")
def delete_election(
    request: Request,
    election_id: int,
    admin: str = Depends(require_admin)
):
    """Archive an election without deleting its history."""
    db = get_db()

    try:
        election = (
            db.query(Election)
            .filter(
                Election.id == election_id,
                Election.is_deleted == False
            )
            .first()
        )

        if not election:
            set_flash(
                request,
                "Election was not found or is already archived."
            )
            return RedirectResponse("/admin/elections", status_code=303)

        if election.blockchain_election_id is None:
            set_flash(
                request,
                "Cannot archive this election because its blockchain mapping is missing."
            )
            return RedirectResponse("/admin/elections", status_code=303)

        from blockchain import (
            cancel_election_on_blockchain,
            get_blockchain_election_status
        )

        blockchain_id = election.blockchain_election_id
        chain_status = get_blockchain_election_status(blockchain_id)

        if chain_status["cancelled"]:
            election.status = "cancelled"

        elif chain_status["closed"]:
            election.status = "closed"

        else:
            cancel_election_on_blockchain(blockchain_id)
            election.status = "cancelled"

        election.is_deleted = True
        db.commit()

        set_flash(
            request,
            "Election archived. Its blockchain record and historical data were preserved."
        )
        return RedirectResponse("/admin/elections", status_code=303)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ============================================================
# EDIT VOTER
# ============================================================

@router.get(
    "/admin/voters/{voter_id}/edit",
    response_class=HTMLResponse
)
def edit_voter_page(
    voter_id: int,
    request: Request,
    admin: str = Depends(require_admin)
):
    db = get_db()

    try:
        voter = (
            db.query(Voter)
            .filter(Voter.id == voter_id)
            .first()
        )

        if not voter:
            raise HTTPException(
                status_code=404,
                detail="Student not found"
            )

        content = f"""
        <div class="card">
            <div class="card-body">
                <h2>Edit Student Details</h2>
                <form method="post" action="/admin/voters/{voter.id}/edit">
                    {csrf_input(request)}
                    <label>Student ID</label>
                    <input name="student_id" value="{safe(voter.student_id)}" required>
                    <label>Email</label>
                    <input type="email" name="email" value="{safe(voter.email)}" required>
                    <div class="action-row">
                        <button class="button" type="submit">Save Changes</button>
                        <a class="button" href="/admin/voters">Cancel</a>
                    </div>
                </form>
            </div>
        </div>
        """

        return HTMLResponse(
            page_template(
                "Edit Student",
                content,
                get_flash(request),
                "voters"
            )
        )

    finally:
        db.close()


@router.post("/admin/voters/{voter_id}/edit")
def edit_voter(
    voter_id: int,
    request: Request,
    student_id: str = Form(...),
    email: str = Form(...),
    admin: str = Depends(require_admin)
):
    db = get_db()

    try:
        voter = (
            db.query(Voter)
            .filter(Voter.id == voter_id)
            .first()
        )

        if not voter:
            raise HTTPException(
                status_code=404,
                detail="Student not found"
            )

        student_id = student_id.strip()
        email = email.strip()

        if not student_id or not email:
            set_flash(
                request,
                "Student ID and email are required."
            )
            return RedirectResponse(
                f"/admin/voters/{voter_id}/edit",
                status_code=303
            )

        duplicate = (
            db.query(Voter)
            .filter(
                Voter.id != voter_id,
                (
                    (Voter.student_id == student_id)
                    | (Voter.email == email)
                )
            )
            .first()
        )

        if duplicate:
            set_flash(
                request,
                "Student ID and email must be unique."
            )
            return RedirectResponse(
                f"/admin/voters/{voter_id}/edit",
                status_code=303
            )

        voter.student_id = student_id
        voter.email = email

        db.commit()

        set_flash(request, "Student details updated successfully.")
        return RedirectResponse("/admin/voters", status_code=303)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ============================================================
# EDIT CANDIDATE
# ============================================================

@router.get(
    "/admin/candidates/{candidate_id}/edit",
    response_class=HTMLResponse
)
def edit_candidate_page(
    candidate_id: int,
    request: Request,
    admin: str = Depends(require_admin)
):
    db = get_db()

    try:
        candidate = (
            db.query(Candidate)
            .filter(Candidate.id == candidate_id)
            .first()
        )

        if not candidate:
            raise HTTPException(
                status_code=404,
                detail="Candidate not found"
            )

        elections = (
            db.query(Election)
            .filter(Election.is_deleted == False)
            .order_by(Election.id.desc())
            .all()
        )

        options = "".join(
            f'<option value="{e.id}" '
            f'{"selected" if e.id == candidate.election_id else ""}>'
            f'{safe(e.title)}</option>'
            for e in elections
        )

        content = f"""
        <div class="card">
            <div class="card-body">
                <h2>Edit Candidate</h2>
                <form method="post" action="/admin/candidates/{candidate.id}/edit">
                    {csrf_input(request)}
                    <label>Name</label>
                    <input name="name" value="{safe(candidate.name)}" required>
                    <label>Position</label>
                    <input name="position" value="{safe(candidate.position)}" required>
                    <label>Election</label>
                    <select name="election_id" required>{options}</select>
                    <div class="action-row">
                        <button class="button" type="submit">Save Changes</button>
                        <a class="button" href="/admin/candidates">Cancel</a>
                    </div>
                </form>
            </div>
        </div>
        """

        return HTMLResponse(
            page_template(
                "Edit Candidate",
                content,
                get_flash(request),
                "candidates"
            )
        )

    finally:
        db.close()


@router.post("/admin/candidates/{candidate_id}/edit")
def edit_candidate(
    candidate_id: int,
    request: Request,
    name: str = Form(...),
    position: str = Form(...),
    election_id: int = Form(...),
    admin: str = Depends(require_admin)
):
    db = get_db()

    try:
        candidate = (
            db.query(Candidate)
            .filter(Candidate.id == candidate_id)
            .first()
        )

        if not candidate:
            raise HTTPException(
                status_code=404,
                detail="Candidate not found"
            )

        current_election = (
            db.query(Election)
            .filter(Election.id == candidate.election_id)
            .first()
        )

        target_election = (
            db.query(Election)
            .filter(
                Election.id == election_id,
                Election.is_deleted == False
            )
            .first()
        )

        name = name.strip()
        position = position.strip()

        if not target_election or not name or not position:
            set_flash(
                request,
                "Enter a valid name and position and select an active election."
            )
            return RedirectResponse(
                f"/admin/candidates/{candidate_id}/edit",
                status_code=303
            )

        if (
            current_election
            and current_election.blockchain_election_id is not None
        ) or target_election.blockchain_election_id is not None:
            set_flash(
                request,
                "Candidates in blockchain-linked elections cannot be edited or reassigned through this form."
            )
            return RedirectResponse("/admin/candidates", status_code=303)

        if current_election and current_election.status != "upcoming":
            set_flash(
                request,
                "Candidates can only be edited while their election is upcoming."
            )
            return RedirectResponse("/admin/candidates", status_code=303)

        candidate.name = name
        candidate.position = position
        candidate.election_id = election_id

        db.commit()

        set_flash(request, "Candidate details updated successfully.")
        return RedirectResponse("/admin/candidates", status_code=303)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ============================================================
# EDIT ELECTION
# ============================================================

@router.get(
    "/admin/elections/{election_id}/edit",
    response_class=HTMLResponse
)
def edit_election_page(
    election_id: int,
    request: Request,
    admin: str = Depends(require_admin)
):
    db = get_db()

    try:
        election = (
            db.query(Election)
            .filter(Election.id == election_id)
            .first()
        )

        if not election:
            raise HTTPException(
                status_code=404,
                detail="Election not found"
            )

        statuses = "".join(
            f'<option value="{value}" '
            f'{"selected" if (election.status or "upcoming").lower() == value else ""}>'
            f'{value.title()}</option>'
            for value in ("upcoming", "ongoing", "closed")
        )

        content = f"""
        <div class="card">
            <div class="card-body">
                <h2>Edit Election Settings</h2>
                <form method="post" action="/admin/elections/{election.id}/edit">
                    {csrf_input(request)}
                    <label>Title</label>
                    <input name="title" value="{safe(election.title)}" required>
                    <label>Description</label>
                    <textarea name="description">{safe(election.description or "")}</textarea>
                    <label>Status</label>
                    <select name="status" required>{statuses}</select>
                    <div class="action-row">
                        <button class="button" type="submit">Save Changes</button>
                        <a class="button" href="/admin/elections">Cancel</a>
                    </div>
                </form>
            </div>
        </div>
        """

        return HTMLResponse(
            page_template(
                "Edit Election",
                content,
                get_flash(request),
                "elections"
            )
        )

    finally:
        db.close()


@router.post("/admin/elections/{election_id}/edit")
def edit_election(
    election_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    status: str = Form(...),
    admin: str = Depends(require_admin)
):
    db = get_db()

    try:
        election = (
            db.query(Election)
            .filter(Election.id == election_id)
            .first()
        )

        if not election:
            raise HTTPException(
                status_code=404,
                detail="Election not found"
            )

        title = title.strip()
        description = description.strip()
        status = status.strip().lower()

        if not title or status not in {
            "upcoming", "ongoing", "closed"
        }:
            set_flash(
                request,
                "Enter a valid title and status."
            )
            return RedirectResponse(
                f"/admin/elections/{election_id}/edit",
                status_code=303
            )

        if election.is_deleted:
            set_flash(
                request,
                "Archived elections cannot be edited."
            )
            return RedirectResponse(
                "/admin/elections",
                status_code=303
            )

        if election.status in {"closed", "cancelled"}:
            set_flash(
                request,
                "Closed or cancelled elections cannot be edited."
            )
            return RedirectResponse(
                f"/admin/elections/{election_id}/edit",
                status_code=303
            )

        if status != election.status:
            set_flash(
                request,
                "Use the dedicated Start, End, or Cancel action to change election status."
            )
            return RedirectResponse(
                f"/admin/elections/{election_id}/edit",
                status_code=303
            )

        if (
            election.blockchain_election_id is not None
            and title != election.title
        ):
            set_flash(
                request,
                "The title of a blockchain-linked election cannot be changed through this form."
            )
            return RedirectResponse(
                f"/admin/elections/{election_id}/edit",
                status_code=303
            )

        election.title = title
        election.description = description

        db.commit()

        set_flash(request, "Election details updated successfully.")
        return RedirectResponse("/admin/elections", status_code=303)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
