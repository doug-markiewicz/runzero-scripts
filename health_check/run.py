import explorers_healthcheck
import tasks_healthcheck
import sites_healthcheck

def main():
    explorers_healthcheck.explorers_healthcheck()
    tasks_healthcheck.tasks_healthcheck()
    sites_healthcheck.sites_healthcheck()

if __name__ == '__main__':
    main()