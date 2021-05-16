# Pitch

### The problem
3000 validators installed кто в лес, кто по дрова -> hard to configure and support, unique problems -> ноды плохо работают, people give up -> low overall cluster efficiency

### Our solution
* SV Manager: A software toolkit to set up and monitor a Solana validator node, including useful alerts and notifications to help you bootstrap and run your node in the most efficient way.
Already implemented:
** Bootstrap the node
** Monitor the node
Planned:
** Disaster recovery
** Receive alerts (Telegram bot etc.)
** Mobile app for alerts, notifications, and node control
** Advanced node monitoring
** Advanced cluster monitoring
** Open API for all data (e.g., to be used by stake bots to select a validator)

For Solana newcomers, it's an easy way to quickly set up the node and monitor it.
For Linux experts, it's a set of useful Ansible scripts to use as references and best practice documents.

* A team to support both the SV Manager project (including toolkit, monitoring dashboard, and various further additional tools) and the Solana community using the toolkit: providing technical support, которая возможна за счет единообразия всех инсталляций.

### Польза для сети:
* Снижаем порог вхождения -> больше народу может поставить ноду -> повышается децентрализация сети
* Повышается эффективность и надежность сети


Competition:
Solanabeach – Explore/Monitor nodes
Validators.app – Monitoring
Stake Economy - Monitoring
Various Node installation guidelines: Github, YouTube, blogs.


Team:
Alexander Ray
