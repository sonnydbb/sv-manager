import time
import solana_rpc as rpc
from common import debug
from common import ValidatorConfig


def get_metrics_from_vote_account_item(item):
    return {
            'epoch_number': item['epochCredits'][-1][0],
            'credits_epoch': item['epochCredits'][-1][1],
            'credits_previous_epoch': item['epochCredits'][-1][2],
            'activated_stake': item['activatedStake'],
            'credits_epoch_delta': item['epochCredits'][-1][1] - item['epochCredits'][-1][2],
            'commission': item['commission']
        }
    

def find_item_in_vote_accounts_section(identity_account_pubkey, section_parent, section_name):
    if section_name in section_parent:
        section = section_parent[section_name]
        for item in section:
            if item['nodePubkey'] == identity_account_pubkey:
                return get_metrics_from_vote_account_item(item)

    return None


def get_vote_account_metrics(vote_accounts_data, identity_account_pubkey):
    """
    get vote metrics from vote account
    :return: 
    voting_status: 0 if validator not found in voting accounts
    voting_status: 1 if validator is current
    voting_status: 2 if validator is delinquent

    """
    result = find_item_in_vote_accounts_section(identity_account_pubkey, vote_accounts_data, 'current')
    if result is not None:
        result.update({'voting_status': 1})
    else:
        result = find_item_in_vote_accounts_section(identity_account_pubkey, vote_accounts_data, 'delinquent')
        if result is not None:
            result.update({'voting_status': 2})
        else:
            result = {'voting_status': 0}
    return result


def get_leader_schedule_metrics(leader_schedule_data, identity_account_pubkey):
    """
    get metrics about leader slots
    """
    if identity_account_pubkey in leader_schedule_data:
        return {"leader_slots_this_epoch": len(leader_schedule_data[identity_account_pubkey])}
    else:
        return {"leader_slots_this_epoch": 0}


def get_block_production_metrics(block_production_data, identity_account_pubkey):
    try:
        item = block_production_data['value']['byIdentity'][identity_account_pubkey]
        return {
            "slots_done": item[0],
            "slots_skipped": item[0] - item[1],
            "blocks_produced": item[1]

        }
    except:
        return {"slots_done": 0, "slots_skipped": 0, "blocks_produced": 0}
       

def get_performance_metrics(performance_sample_data, epoch_info_data, leader_schedule_by_identity):

    if len(performance_sample_data) > 0:
        sample = performance_sample_data[0]
        mid_slot_time = sample['samplePeriodSecs'] / sample['numSlots']
        current_slot_index = epoch_info_data['slotIndex']
        remaining_time = (epoch_info_data["slotsInEpoch"] - current_slot_index)*mid_slot_time
        epoch_end_time = round(time.time()) + remaining_time
        time_until_next_slot = -1
        if leader_schedule_by_identity is not None:
            for slot in leader_schedule_by_identity:
                if current_slot_index < slot:
                    next_slot = slot
                    time_until_next_slot = (next_slot - current_slot_index)*mid_slot_time
                    break
        else:
            time_until_next_slot = None

        result = {
            "epoch_endtime": epoch_end_time,
            "epoch_remaining_sec": remaining_time
        }

        if time_until_next_slot is not None:
            result.update({"time_until_next_slot": time_until_next_slot})
    else:
        result = {}

    return result


def get_balance_metric(balance_data, key: str):
    if 'value' in balance_data:
        result = {key: balance_data['value']}
    else:
        result = {}

    return result


def get_solana_version_metric(solana_version_data):
    if solana_version_data is not None:
        if 'solana-core' in solana_version_data:
            return {'solana_version': solana_version_data['solana-core']}

    return {}


def get_current_stake_metric(stake_data):
    active = 0
    activating = 0
    deactivating = 0
    for item in stake_data:
        active = active + item.get('activeStake', 0)
        activating = activating + item.get('activatingStake', 0)
        deactivating = deactivating + item.get('deactivatingStake', 0)

    return {'active_stake': active, 'activating_stake': activating, 'deactivating_stake': deactivating}


def load_data(config: ValidatorConfig):
    identity_account_pubkey = rpc.load_identity_account_pubkey(config)
    vote_account_pubkey = rpc.load_vote_account_pubkey(config)

    if (identity_account_pubkey is not None) and (vote_account_pubkey is not None):
        identity_account_balance_data = rpc.load_identity_account_balance(config, identity_account_pubkey)
        vote_account_balance_data = rpc.load_vote_account_balance(config, vote_account_pubkey)
        epoch_info_data = rpc.load_epoch_info(config)
        leader_schedule_data = rpc.load_leader_schedule(config, identity_account_pubkey)
        block_production_data = rpc.load_block_production(config, identity_account_pubkey)
        vote_accounts_data = rpc.load_vote_accounts(config, vote_account_pubkey)
        performance_sample_data = rpc.load_recent_performance_sample(config)
        solana_version_data = rpc.load_solana_version(config)
        stakes_data = rpc.load_stakes(vote_account_pubkey)

        result = {
            'identity_account_pubkey': identity_account_pubkey,
            'vote_account_pubkey': vote_account_pubkey,
            'identity_account_balance':  identity_account_balance_data,
            'vote_account_balance': vote_account_balance_data,
            'epoch_info': epoch_info_data,
            'leader_schedule': leader_schedule_data,
            'block_production': block_production_data,
            'vote_accounts': vote_accounts_data,
            'performance_sample': performance_sample_data,
            'solana_version_data': solana_version_data,
            'stakes_data': stakes_data
        }

        debug(config, str(result))

        return result
    else:
        return None


def calculate_influx_fields(data):
    if data is None:
        result = {"validator_status": 0}
    else:
        identity_account_pubkey = data['identity_account_pubkey']

        vote_account_metrics = get_vote_account_metrics(data['vote_accounts'], identity_account_pubkey)
        leader_schedule_metrics = get_leader_schedule_metrics(data['leader_schedule'], identity_account_pubkey)
        epoch_metrics = data['epoch_info']
        block_production_metrics = get_block_production_metrics(data['block_production'], identity_account_pubkey)
        if identity_account_pubkey in data['leader_schedule']:
            leader_schedule_by_identity = data['leader_schedule'][identity_account_pubkey]
        else:
            leader_schedule_by_identity = None

        performance_metrics = get_performance_metrics(
            data['performance_sample'], epoch_metrics, leader_schedule_by_identity)

        result = {"validator_status": 1}
        result.update(vote_account_metrics)
        result.update(leader_schedule_metrics)
        result.update(epoch_metrics)
        result.update(block_production_metrics)
        result.update(performance_metrics)
        result.update(get_balance_metric(data['identity_account_balance'], 'identity_account_balance'))
        result.update(get_balance_metric(data['vote_account_balance'], 'vote_account_balance'))
        result.update(get_current_stake_metric(data['stakes_data']))

    result.update({"monitoring_version": 1})

    return result


def calculate_influx_data(config: ValidatorConfig):

    data = load_data(config)

    influx_measurement = {
        "measurement": "validators_info",
        "time": round(time.time() * 1000),
        "validator_name": config.validator_name,
        "fields": calculate_influx_fields(data)
    }

    if data is not None and 'solana_version_data' in data:
        influx_measurement.update(get_solana_version_metric(data['solana_version_data']))

    return influx_measurement
