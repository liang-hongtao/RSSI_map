import numpy as np
import matplotlib.pyplot as plt
import matlab.engine
import os
from tqdm import tqdm
from pykrige.ok import OrdinaryKriging
from scipy.interpolate import griddata
from PIL import Image
import math

def generate_gif(frames_dir, output_gif_path, duration=100):
    """
    从指定文件夹中的图片生成 GIF 动态图片。

    参数:
        frames_dir (str): 保存帧图片的文件夹路径。
        output_gif_path (str): 输出 GIF 文件路径。
        duration (int): 每帧显示时间（毫秒）。
    """
    try:
        # 获取文件夹中所有图片文件，并按文件名排序
        frame_files = sorted(
            [os.path.join(frames_dir, file) for file in os.listdir(frames_dir) if file.endswith(('.png', '.jpg', '.jpeg'))]
        )

        if not frame_files:
            print("未找到图片文件，无法生成 GIF。")
            return

        # 打开所有图片
        images = [Image.open(frame) for frame in frame_files]

        # 保存为 GIF
        images[0].save(
            output_gif_path,
            save_all=True,
            append_images=images[1:],
            optimize=False,
            duration=duration,
            loop=0  # 无限循环
        )
        print(f"GIF 动态图片已成功保存到: {output_gif_path}")

    except Exception as e:
        print(f"生成 GIF 时发生错误: {e}")
        
        
class SpectrumMapEstimator:
    def __init__(self, x_min=-50, x_max=50, y_min=-50, y_max=50, fbl_x=25, fbl_y=25,interpolation_method='idw'):
        self.map_size = (fbl_x, fbl_y)
        self.spectrum_map = np.full(self.map_size, np.nan)  # 创建频谱地图（未填写的地方用NaN填充）
        self.spectrum_map_full = np.full(self.map_size, np.nan)
        self.max_rssi_position = None
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.fbl_x = fbl_x
        self.fbl_y = fbl_y
        self.relation_dict_x = {}
        self.relation_dict_y = {}
        x_linspace = np.linspace(x_min, x_max, fbl_x)
        for index, element in enumerate(x_linspace):
            self.relation_dict_x[element] = int(index)
        y_linspace = np.linspace(y_min, y_max, fbl_y)
        for index, element in enumerate(y_linspace):
            self.relation_dict_y[element] = int(index)
            
        self.positions = []  # 存储接收点的坐标
        self.rss_values = []  # 存储接收点的信号强度
        self.interpolation_method = interpolation_method
        

    def add_measurement(self, position, rssi):
        self.positions.append(position)
        self.rss_values.append(rssi)
        ix = self.relation_dict_x[position[0]]
        iy = self.relation_dict_y[position[1]]
        self.spectrum_map[ix, iy] = rssi


    def update_spectrum_map_full(self):
        # 使用不同的插值方法补全频谱地图
        if len(self.positions) >= 3:  # 至少有3个点进行插值
            positions_array = np.array(self.positions)
            x = positions_array[:, 0]
            y = positions_array[:, 1]
            z = np.array(self.rss_values)
            # 创建网格
            grid_x, grid_y = np.meshgrid(np.linspace(self.x_min, self.x_max, self.fbl_x), np.linspace(self.y_min, self.y_max, self.fbl_y))

            if self.interpolation_method == 'kriging':
                # 使用克里金插值
                OK = OrdinaryKriging(x, y, z, variogram_model='spherical', verbose=False, enable_plotting=False)
                grid_z, _ = OK.execute('grid', grid_x, grid_y)
                if not np.all(np.isnan(grid_z)):
                    self.spectrum_map_full = np.flipud(np.rot90(grid_z))

            elif self.interpolation_method == 'idw':
                # 反距离加权插值（IDW）
                grid_z = griddata((x, y), z, (grid_x, grid_y), method='nearest')  # 这里使用最近邻近似IDW
                if not np.all(np.isnan(grid_z)):
                    self.spectrum_map_full = np.flipud(np.rot90(grid_z))

            elif self.interpolation_method == 'spline':
                # 样条插值
                grid_z = griddata((x, y), z, (grid_x, grid_y), method='cubic')  # 使用三次样条插值
                if not np.all(np.isnan(grid_z)):
                    self.spectrum_map_full = np.flipud(np.rot90(grid_z))

            elif self.interpolation_method == 'linear':
                # 线性插值
                grid_z = griddata((x, y), z, (grid_x, grid_y), method='linear')
                if not np.all(np.isnan(grid_z)):
                    self.spectrum_map_full = np.flipud(np.rot90(grid_z))

            elif self.interpolation_method == 'nearest':
                # 最近邻插值
                grid_z = griddata((x, y), z, (grid_x, grid_y), method='nearest')
                if not np.all(np.isnan(grid_z)):
                    self.spectrum_map_full = np.flipud(np.rot90(grid_z))
                    
                    
            # 找到频谱图中RSSI值最大的点
            self.max_rssi_index = self.calculate_center()
            # 将该索引位置转换为现实世界坐标
            for key, value in self.relation_dict_x.items():
                if value == self.max_rssi_index[0]:
                    max_x = key        
            for key, value in self.relation_dict_y.items():
                if value == self.max_rssi_index[1]:
                    max_y = key
            self.max_rssi_position = (max_x, max_y)
                    

    def calculate_center(self):
        max_value = np.nanmax(self.spectrum_map_full)
        max_indices = np.argwhere(self.spectrum_map_full == max_value)
        x_coords = max_indices[:, 0]
        y_coords = max_indices[:, 1]
        center_x = np.mean(x_coords)
        center_y = np.mean(y_coords)
        return np.round(center_x), np.round(center_y)
    
    
    def save_be_map(self, filename):
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))  # 只使用一个子图，避免白色空格问题
        # 绘制频谱地图（使用 NaN 填充没有数据的区域）
        im1 = axes[0].imshow(self.spectrum_map, cmap="jet", origin="lower", extent=[self.x_min, self.x_max, self.y_min, self.y_max])
        axes[0].set_title("Spectrum Map (RSSI)")
        axes[0].set_xlim(self.x_min, self.x_max)
        axes[0].set_ylim(self.y_min, self.y_max)
        axes[0].set_xlabel("X Position (m)")
        axes[0].set_ylabel("Y Position (m)")
        fig.colorbar(im1, ax=axes[0], label="RSSI (dBm)")  # 添加颜色条

        # 绘制插值后的频谱图
        im2 = axes[1].imshow(self.spectrum_map_full, cmap="jet", origin="lower", extent=[self.x_min, self.x_max, self.y_min, self.y_max])
        axes[1].set_title(f"Interpolated Map ({self.interpolation_method.capitalize()})")
        axes[1].set_xlim(self.x_min, self.x_max)
        axes[1].set_ylim(self.y_min, self.y_max)
        axes[1].set_xlabel("X Position (m)")
        axes[1].set_ylabel("Y Position (m)")
        fig.colorbar(im2, ax=axes[1], label="RSSI (dBm)")  # 添加颜色条
        axes[1].scatter(self.max_rssi_position[1], self.max_rssi_position[0], color='white', marker='x', s=100, label='Max RSSI Position')
        axes[1].legend()
        
        # 保存图像
        plt.tight_layout()
        plt.savefig(filename)
        plt.close()
        
    def plot_error(self,distances,error_path):
        # 设置图形大小
        plt.figure(figsize=(8, 6))
        # 绘制折线图
        plt.plot(range(len(distances)), distances, marker='o', markersize=4, linewidth=1.5)
        plt.xlabel('Step')
        plt.ylabel('Distance')
        plt.title('Distance between Max RSSI Position and Transmitter Position')
        # 设置坐标轴范围从 0 开始
        plt.xlim(0, len(distances))
        plt.ylim(0, max(distances) * 1.1 if distances else 1)  # 给纵轴留一点余量，如果 distances 为空则设为 1
        # 添加网格线
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        # 设置刻度字体大小
        plt.xticks(fontsize=10)
        plt.yticks(fontsize=10)
        # 保存图片
        plt.savefig(error_path)
        plt.close()


def test(method,shuffle):
    print("Start MATLAB Engine...")
    matlab_eng = matlab.engine.start_matlab()
    current_directory = os.path.abspath(os.getcwd())
    matlab_eng.addpath(os.path.join(current_directory, "src_v4.2.1", "matlab"))  # 加载MATLAB路径
    current_path = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(current_path, f"../output/spectrum_map/{method}/{shuffle}/")
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    error_path = os.path.join(current_path, f"../output/spectrum_map/{method}_{shuffle}_distance_plot.png")
    print("MATLAB Engine started successfully!")
    i = 0
    transmitter_position_x = 20
    transmitter_position_y = 40
    transmitter_position = [[transmitter_position_y], [transmitter_position_x], [0.0]]
    transmitter_position_matlab = matlab.double(transmitter_position)
    x_min = -50
    x_max = 50
    y_min = -50
    y_max = 50
    fbl_x = 25
    fbl_y = 25
    
    receiver_positions = np.array([[[x], [y], [0.0]] for x in np.linspace(x_min, x_max, fbl_x) for y in np.linspace(y_min, y_max, fbl_y)])
    if shuffle:
        np.random.shuffle(receiver_positions)
    distances = []
    estimator = SpectrumMapEstimator(x_min, x_max, y_min, y_max, fbl_x, fbl_y, interpolation_method=method)
    for position in tqdm(receiver_positions):
        position_matlab = matlab.double(position)
        rssi = matlab_eng.close_in_v2("unreal_envs.stl", position_matlab, transmitter_position_matlab)
        estimator.add_measurement([position[0][0], position[1][0]], rssi)
        if (i + 1) % 3 == 0:
            estimator.update_spectrum_map_full()
            estimator.save_be_map(filename=f"{output_path}spectrum_map_{i:04d}.png")
            x, y = estimator.max_rssi_position
            transmitter_x = transmitter_position[0][0]
            transmitter_y = transmitter_position[1][0]
            distance = math.sqrt((x - transmitter_x) ** 2 + (y - transmitter_y) ** 2)
            distances.append(distance)
            estimator.plot_error(distances, error_path)
        i += 1

    matlab_eng.quit()  # 关闭MATLAB引擎，释放资源
    output_gif_path = os.path.join(current_path, f"../output/spectrum_map/{method}_{shuffle}.gif")
    generate_gif(output_path, output_gif_path, duration=150)


if __name__ == "__main__":
    shuffle = True
    test('linear', shuffle)
    test('spline', shuffle)
    test('nearest', shuffle)
    test('idw',shuffle)