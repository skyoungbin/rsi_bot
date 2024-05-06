from plotly.subplots import make_subplots
import plotly.graph_objects as go

def create_chart(df):
    # 서브플롯 생성
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=('Price and RSI', 'Volume'),
                        vertical_spacing=0.1,
                        specs=[[{"secondary_y": True}], [{}]],
                        row_heights=[0.8, 0.2])  

    # 캔들스틱 그래프 추가
    fig.add_trace(go.Candlestick(x=df.index,
                                 open=df['open'], high=df['high'],
                                 low=df['low'], close=df['close']),
                  row=1, col=1)

    # df에 'rsi' 컬럼이 있는지 확인
    if 'rsi' in df.columns:
        # RSI 그래프 추가
        fig.add_trace(go.Scatter(x=df.index, y=df['rsi'],
                                 mode='lines',
                                 name='rsi'),
                      secondary_y=True,
                      row=1, col=1)


    # 레이아웃 업데이트
    fig.update_layout(
        yaxis=dict(
            title='Price',
            titlefont=dict(
                color="#1f77b4"
            ),
            tickfont=dict(
                color="#1f77b4"
            )),
        yaxis2=dict(
            title='RSI',
            titlefont=dict(
                color="#ff7f0e"
            ),
            tickfont=dict(
                color="#ff7f0e"
            ),
            overlaying='y',
            side='right'
        ),
        xaxis=dict(
            rangeslider=dict(
                visible=False  # Range Slider 제거
            ),
            type='date'
        )
    )

    # 거래량 그래프 추가
    fig.add_trace(go.Bar(x=df.index, y=df['volume']),
                  row=2, col=1)

    return fig

def create_bot_chart(df):
    # 서브플롯 생성
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=('Price and position', 'Volume'),
                        vertical_spacing=0.1,
                        specs=[[{"secondary_y": True}], [{}]],
                        row_heights=[0.8, 0.2])  

    # 캔들스틱 그래프 추가
    fig.add_trace(go.Candlestick(x=df.index,
                                 open=df['open'], high=df['high'],
                                 low=df['low'], close=df['close']),
                  row=1, col=1)


    # position 그래프 추가
    fig.add_trace(go.Scatter(x=df.index, y=df['position'],
                                mode='lines',
                                name='rsi'),
                    secondary_y=True,
                    row=1, col=1)


    # 레이아웃 업데이트
    fig.update_layout(
        yaxis=dict(
            title='Price',
            titlefont=dict(
                color="#1f77b4"
            ),
            tickfont=dict(
                color="#1f77b4"
            )),
        yaxis2=dict(
            title='Position',
            titlefont=dict(
                color="#ff7f0e"
            ),
            tickfont=dict(
                color="#ff7f0e"
            ),
            overlaying='y',
            side='right'
        ),
        xaxis=dict(
            rangeslider=dict(
                visible=False  # Range Slider 제거
            ),
            type='date'
        )
    )

    # 거래량 그래프 추가
    fig.add_trace(go.Bar(x=df.index, y=df['volume']),
                  row=2, col=1)

    return fig
# def create_chart(df, df2):
#     # 서브플롯 생성
#     fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
#                         subplot_titles=('Price and RSI', 'Volume'),
#                         vertical_spacing=0.1,
#                         specs=[[{"secondary_y": True}], [{}]],
#                         row_heights=[0.8, 0.2])  

#     # 캔들스틱 그래프 추가
#     fig.add_trace(go.Candlestick(x=df.index,
#                                  open=df['open'], high=df['high'],
#                                  low=df['low'], close=df['close']),
#                   row=1, col=1)

#     # RSI 그래프 추가
#     fig.add_trace(go.Scatter(x=df.index, y=df['rsi'],
#                              mode='lines',
#                              name='rsi'),
#                   secondary_y=True,
#                   row=1, col=1)

#     # LIVE_RSI 그래프 추가
#     fig.add_trace(go.Scatter(x=df2.index, y=df2['rsi'],
#                              mode='lines',
#                              name='live_rsi',
#                              opacity=0.6),
#                   secondary_y=True,
#                   row=1, col=1)


#     # 레이아웃 업데이트
#     fig.update_layout(
#         yaxis=dict(
#             title='Price',
#             titlefont=dict(
#                 color="#1f77b4"
#             ),
#             tickfont=dict(
#                 color="#1f77b4"
#             )),
#         yaxis2=dict(
#             title='RSI',
#             titlefont=dict(
#                 color="#ff7f0e"
#             ),
#             tickfont=dict(
#                 color="#ff7f0e"
#             ),
#             overlaying='y',
#             side='right'
#         ),
#         xaxis=dict(
#             rangeslider=dict(
#                 visible=False  # Range Slider 제거
#             ),
#             type='date'
#         )
#     )

#     # 거래량 그래프 추가
#     fig.add_trace(go.Bar(x=df.index, y=df['volume']),
#                   row=2, col=1)

#     return fig



# def create_chart(df):
#     # 그래프 생성
#     fig = go.Figure(data=[go.Candlestick(x=df.index,
#                                          open=df['open'], high=df['high'],
#                                          low=df['low'], close=df['close'])])

#     fig.add_trace(go.Scatter(x=df.index, y=df['rsi'],
#                              mode='lines',
#                              name='rsi'))
#     return fig


# def create_chart(df):
#     # 캔들스틱 그래프 생성
#     fig = go.Figure()
#     fig.add_trace(go.Candlestick(x=df.index,
#                                  open=df['open'], high=df['high'],
#                                  low=df['low'], close=df['close'],
#                                  yaxis='y2'))  # y2 축을 사용

#     # RSI 그래프 생성
#     fig.add_trace(go.Scatter(x=df.index, y=df['rsi'],
#                              mode='lines',
#                              name='rsi'))

#     # 레이아웃 설정 (두 개의 y축 설정)
#     fig.update_layout(
#         xaxis=dict(
#             rangeslider=dict(
#                 visible=False  # 여기를 False로 설정
#             ),
#             type='date'
#         ),
#         yaxis=dict(
#             title='RSI',
#             titlefont=dict(
#                 color="#1f77b4"
#             ),
#             tickfont=dict(
#                 color="#1f77b4"
#             )
#         ),
#         yaxis2=dict(
#             title='Price',
#             titlefont=dict(
#                 color="#ff7f0e"
#             ),
#             tickfont=dict(
#                 color="#ff7f0e"
#             ),
#             overlaying='y',
#             side='right'
#         )
#     )

#     return fig