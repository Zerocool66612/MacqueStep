# MacaqueSTEP technical conformance roadmap

Engineering target: POSIX.1-2024 / Single UNIX Specification Version 5.
Status: proposed target, not verified. No certification or complete conformance claim.

The desktop preview is an application on the host OS. Its Unix Readiness Inventory reports that host, not a separate MacaqueSTEP kernel or installed image. Presence of utilities and sysconf values does not establish required behavior.

1. Select and freeze the OS release, architecture, libc, shell, utility versions, feature options, and supported environment.
2. Create a requirement-by-requirement matrix from the selected specifications. Record mandatory requirements, applicable options, implementation-defined behavior, evidence, failures, and exclusions with reasons.
3. Cover headers, types, C interfaces, process and signal behavior, filesystems, permissions, terminal interfaces, threads, synchronization, time, shell language, utilities, locales, and error handling as applicable to that target.
4. Run suitable tests in isolated environments, record exact configuration and results, investigate failures, implement fixes, and retest affected areas. A hand-picked smoke test or utility inventory cannot substitute for full coverage.
5. Supply required conformance documentation and repeat validation on the installed image and target hardware. Track regressions with every release.

Standards references:
- https://www.unix.org/overview.html
- https://pubs.opengroup.org/onlinepubs/9799919799/
- https://www.unix.org/the_brand.html

Technical conformance work and formal certification are separate. This project does not claim UNIX certification or use a certification logo.
