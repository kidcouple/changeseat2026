import cairosvg
import os

def generate_icons():
    # static 디렉토리가 없으면 생성
    if not os.path.exists('static'):
        os.makedirs('static')
    
    # SVG를 PNG로 변환
    cairosvg.svg2png(url='static/icon.svg',
                     write_to='static/icon-192x192.png',
                     output_width=192,
                     output_height=192)
    
    cairosvg.svg2png(url='static/icon.svg',
                     write_to='static/icon-512x512.png',
                     output_width=512,
                     output_height=512)

if __name__ == '__main__':
    generate_icons() 