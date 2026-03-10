document.addEventListener("DOMContentLoaded", () => {
    const navbar = document.querySelector(".top-navbar");
    const navMenu = document.querySelector(".nav-menu");
    const navToggle = document.querySelector(".nav-toggle");
    const navLinks = document.querySelectorAll('.nav-menu a[href^="#"]');
    const sections = document.querySelectorAll("section[id]");

    const revealElements = document.querySelectorAll(
        ".hero-copy, .section-heading, .info-card, .pricing-table-wrapper, .contact-card, .bottom-contact-item"
    );

    revealElements.forEach(el => el.classList.add("reveal"));

    const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add("is-visible");
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.12
    });

    revealElements.forEach(el => revealObserver.observe(el));

    function handleNavbarScroll() {
        if (window.scrollY > 20) {
            navbar.classList.add("scrolled");
        } else {
            navbar.classList.remove("scrolled");
        }
    }

    function updateActiveNav() {
        const navHeight = navbar ? navbar.offsetHeight : 0;
        const scrollPosition = window.scrollY + navHeight + 80;

        let currentSectionId = "";

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;
            const sectionId = section.getAttribute("id");

            if (
                scrollPosition >= sectionTop &&
                scrollPosition < sectionTop + sectionHeight
            ) {
                currentSectionId = sectionId;
            }
        });

        navLinks.forEach(link => {
            link.classList.remove("active");
            const href = link.getAttribute("href");

            if (href === `#${currentSectionId}`) {
                link.classList.add("active");
            }
        });
    }

    function closeMenu() {
        if (navMenu) navMenu.classList.remove("open");
        document.body.classList.remove("menu-open");
    }

    if (navToggle) {
        navToggle.addEventListener("click", () => {
            navMenu.classList.toggle("open");
            document.body.classList.toggle("menu-open");
        });
    }

    navLinks.forEach(link => {
        link.addEventListener("click", (e) => {
            e.preventDefault();

            const targetId = link.getAttribute("href");
            const target = document.querySelector(targetId);

            if (!target) return;

            const navHeight = navbar ? navbar.offsetHeight : 0;
            const targetTop = target.getBoundingClientRect().top + window.scrollY - navHeight + 2;

            window.scrollTo({
                top: targetTop,
                behavior: "smooth"
            });

            closeMenu();
        });
    });

    document.addEventListener("click", (e) => {
        if (!navMenu || !navToggle) return;

        const clickedInsideMenu = navMenu.contains(e.target);
        const clickedToggle = navToggle.contains(e.target);

        if (!clickedInsideMenu && !clickedToggle) {
            closeMenu();
        }
    });

    handleNavbarScroll();
    updateActiveNav();

    window.addEventListener("scroll", () => {
        handleNavbarScroll();
        updateActiveNav();
    });

    window.addEventListener("resize", closeMenu);
});