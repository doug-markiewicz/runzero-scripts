import explorers_healthcheck
import tasks_healthcheck

def main():
    explorers_healthcheck.explorers_healthcheck()
    tasks_healthcheck.tasks_healthcheck()

if __name__ == '__main__':
    main()