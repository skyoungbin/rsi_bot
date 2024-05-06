




def calculate_count_from_days_ago(interval_minutes, days_ago):
    """
    :param interval_minutes: 데이터 포인트 간의 간격 (분 단위)
    :param days_ago: 현재로부터 몇 일 전까지의 데이터를 가져올지 지정

    """
    # 하루의 총 분 수를 계산
    minutes_in_a_day = 24 * 60
    
    # 총 필요한 데이터 포인트 수를 계산
    total_minutes = days_ago * minutes_in_a_day
    count = total_minutes // interval_minutes
    
    return count
