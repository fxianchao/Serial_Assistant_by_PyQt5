import os.path
# import logging
from PyQt5.QtCore import QDateTime, QTimer, QByteArray, QIODevice
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtWidgets import (QMainWindow, QMessageBox, QStyleFactory, QLabel,
                             QFileDialog)
from Ui_serial import Ui_MainWindow as Ui_serial

CUR_PATH = os.path.dirname(__file__)


class Serial(QMainWindow, Ui_serial):
    """ 开始界面 """

    def __init__(self, parent=None):
        super(Serial, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("串口助手<V1.0> by-FXC")  # 设置标题
        self._num_send = 0  # 发送数据量
        self._num_receive = 0  # 接收数据量
        self._serial = QSerialPort(self)  # 用于连接串口的对象
        self._single_slot()  # 连接信号与槽
        self.get_available_ports()  # 获取可用的串口列表
        self.set_statusbar()  # 设置状态栏
        self.plainTextEdit_send.setPlainText("hello world!")

    def _single_slot(self):
        # 信号与槽的连接
        self._serial.readyRead.connect(self.receive_data)  # 绑定数据读取信号
        self.pushButton_connect.clicked.connect(self.open_close_port)  # 打开关闭串口
        self.pushButton_send.clicked.connect(self.send_data)  # 发送数据
        self.pushButton_clear_receive.clicked.connect(
            self.clear_receive)  # 清除接收窗口
        self.pushButton_clear_send.clicked.connect(self.clear_send)  # 清除发送窗口
        self.pushButton_flush.clicked.connect(self.get_available_ports)  # 刷新
        self.pushButton_open_file.clicked.connect(self._open_file)  # 打开文件
        self.pushButton_send_file.clicked.connect(self._send_file)  # 发送文件

    def set_statusbar(self):
        # 设置状态栏
        self._timer_one_s = QTimer(self)
        self._timer_one_s.timeout.connect(self._update_datetime)
        self._label_datetime = QLabel(self.statusbar)
        self._label_datetime.setText(" " * 30)
        self._label_num_send = QLabel(self.statusbar)
        self._label_num_recv = QLabel(self.statusbar)
        self._label_num_send.setText("发送:" + str(self._num_send))
        self._label_num_recv.setText("接收:" + str(self._num_receive))
        self.statusbar.addPermanentWidget(self._label_num_send, stretch=0)
        self.statusbar.addPermanentWidget(self._label_num_recv, stretch=0)
        self.statusbar.addPermanentWidget(self._label_datetime, stretch=0)
        self._timer_one_s.start(500)

    def _update_datetime(self):
        # 更新实时时间
        _real_time = QDateTime.currentDateTime().toString(
            " yyyy-MM-dd hh:mm:ss ")
        self._label_datetime.setText(_real_time)

    def get_available_ports(self):
        # 获取可用的串口
        self._ports = {}  # 用于保存串口的信息
        self.comboBox_port.clear()
        ports = QSerialPortInfo.availablePorts()  # 获取串口信息,返回一个保存串口信息的对象
        if not ports:
            self.statusbar.showMessage("无可用串口!", 5000)
            return
        ports.reverse()  # 逆序
        for port in ports:
            # 通过串口名字关联串口变量,并将其添加到界面控件中
            # print(port.standardBaudRates())
            self._ports[port.portName()] = port
            self.comboBox_port.addItem(port.portName())

    def open_close_port(self, ):
        # 打开,关闭串口
        if self._serial.isOpen():
            # 如果串口处于开启状态
            self._serial.close()
            self.statusbar.showMessage("关闭串口成功", 2000)
            self.pushButton_connect.setText("打开串口")
            self.label_status.setProperty("isOn", False)
            self.label_status.style().polish(self.label_status)  # 刷新样式
            return

        if self.comboBox_port.currentText():
            # print(self.comboBox_port.currentText())
            port = self._ports[self.comboBox_port.currentText()]
            # 设置端口
            self._serial.setPort(port)
            # 设置波特率
            self._serial.setBaudRate(  # QSerialPort::Baud9600
                getattr(QSerialPort,
                        'Baud' + self.comboBox_baud.currentText()))
            # 设置校验位
            self._serial.setParity(  # QSerialPort::NoParity
                getattr(QSerialPort,
                        self.comboBox_parity.currentText() + 'Parity'))
            # 设置数据位
            self._serial.setDataBits(  # QSerialPort::Data8
                getattr(QSerialPort,
                        'Data' + self.comboBox_data.currentText()))
            # 设置停止位
            self._serial.setStopBits(  # QSerialPort::OneStop
                getattr(QSerialPort, self.comboBox_stop.currentText()))

            # NoFlowControl          没有流程控制
            # HardwareControl        硬件流程控制(RTS/CTS)
            # SoftwareControl        软件流程控制(XON/XOFF)
            # UnknownFlowControl     未知控制
            self._serial.setFlowControl(QSerialPort.NoFlowControl)
            # 以读写方式打开串口
            ok = self._serial.open(QIODevice.ReadWrite)
            if ok:
                self.statusbar.showMessage("打开串口成功", 2000)
                self.pushButton_connect.setText('关闭串口')
                self.label_status.setProperty("isOn", True)
                self.label_status.style().polish(self.label_status)  # 刷新样式
            else:
                QMessageBox.warning(self, "警告", "打开串口失败", QMessageBox.Yes)
                # self.statusbar.showMessage('打开串口失败', 2000)
                self.pushButton_connect.setText('打开串口')
                self.label_status.setProperty("isOn", False)
                self.label_status.style().polish(self.label_status)  # 刷新样式
        else:
            QMessageBox.warning(self, "警告", "无可用串口", QMessageBox.Yes)

    def receive_data(self, ):
        # 接收数据
        num = self._serial.bytesAvailable()
        if num:
            self._num_receive += num
            self._label_num_recv.setText("接收:" + str(self._num_receive))
            # print(num)
            # 当数据可读取时
            # 这里只是简答测试少量数据,如果数据量太多了此处readAll其实并没有读完
            # 需要自行设置粘包协议
            _data = self._serial.readAll()
            # print("接收数据", _data)

            if self.checkBox_show_current_time.isChecked():
                _real_time = QDateTime.currentDateTime().toString(
                    "yyyy-MM-dd hh:mm:ss")
                real_time = (
                    "<span style='text-decoration:underline; color:green; font-size:12px;'>"
                    + _real_time + "</span>")
                self.textBrowser_receive.append(real_time)
                self.textBrowser_receive.append("")
            if self.radioButton_asciiview.isChecked():
                data = _data.data()
                # 解码显示
                try:
                    self.textBrowser_receive.insertPlainText(
                        data.decode('utf-8'))
                except:  # 解码失败
                    out_s = (
                        r"<span style='text-decoration:underline; color:red; font-size:16px;'>"
                        + r"解码失败" + repr(data) + r"</span>")
                    # self.textBrowser_receive.insertPlainText(out_s)
                    self.textBrowser_receive.append(out_s)
            elif self.radioButton_hexview.isChecked():
                data = _data.data()
                out_s = ''
                for i in range(0, len(data)):
                    out_s = out_s + '0x{:02X}'.format(data[i]) + ' '
                self.textBrowser_receive.insertPlainText(out_s)

    def send_data(self, ):
        # 发送数据
        if not self._serial.isOpen():
            QMessageBox.warning(self, "警告", "串口未打开!", QMessageBox.Yes)
            return
        _text = self.plainTextEdit_send.toPlainText()
        # print(_text)
        if not _text:
            QMessageBox.warning(self, "警告", "没有发送数据!", QMessageBox.Yes)
            return
        if self.radioButton_asciisend.isChecked():
            text = QByteArray(_text.encode('utf-8'))  # 编码
            # print("发送数据", text)
            # self._serial.write(text)
        elif self.radioButton_hexsend.isChecked():
            _text = _text.strip().upper()  # 去除两边的空格,转换为大写
            if not _text:
                QMessageBox.warning(self, "警告", "发送数据错误!", QMessageBox.Yes)
                return
            # print("处理数据", _text)
            _list = _text.split()
            # print(_list)

            for i in range(len(_list)):
                if self._is_hex(_list[i]):
                    if len(_list[i]) > 2:
                        QMessageBox.warning(self, "警告", "发送数据输入格式错误!",
                                            QMessageBox.Yes)
                        return
                else:
                    QMessageBox.warning(self, "警告", "发送数据不是十六进制数据!",
                                        QMessageBox.Yes)
                    return
            _text = "".join(_list)
            # print(_text)
            text = QByteArray.fromHex(_text.encode('utf-8'))  # 编码
            # print("发送数据", text)
        _num = self._serial.write(text)
        self._num_send += _num
        self._label_num_send.setText("发送:" + str(self._num_send))

    # def _is_hex(self, s):
    #     # 验证十六进制
    #     try:
    #         int(s, 16)
    #         return True
    #     except ValueError:
    #         return False

    def clear_receive(self):
        # 清除接收窗口
        self.textBrowser_receive.clear()
        self._num_receive = 0
        self._label_num_recv.setText("发送:" + str(self._num_receive))
        self.statusbar.showMessage("清除接收窗口", 1000)

    def clear_send(self):
        # 清除发送窗口
        self.plainTextEdit_send.clear()
        self._num_send = 0
        self._label_num_send.setText("发送:" + str(self._num_send))
        self.statusbar.showMessage("清除发送窗口", 1000)

    def _open_file(self, ):
        # 打开文件
        # QFileDialog.getOpenFileName参数
        # 第一个参数指定父控件
        # 第二个参数是打开对话框的标题
        # 第三个参数是默认打开的目录,不同平台下不同
        # 第四个参数是对话框中文件扩展名过滤器.
        fname, ftype = QFileDialog.getOpenFileName(self, '打开文件', CUR_PATH,
                                                   "All files (*)")
        # print(fname, "->", ftype)
        if fname:
            _old_text = self.plainTextEdit_send.toPlainText()
            try:
                with open(fname, "r", encoding="utf-8") as f:
                    self.plainTextEdit_send.clear()
                    self.plainTextEdit_send.setPlainText(f.read())
                    self.lineEdit_filename.setText(fname)
            except:
                self.plainTextEdit_send.setPlainText(_old_text)
                self.lineEdit_filename.clear()
                QMessageBox.warning(self, "警告", "解码失败!", QMessageBox.Yes)
        else:
            self.statusbar.clearMessage()
            self.statusbar.showMessage("没有选择文件", 5000)

    def _send_file(self, ):
        # 发送文件
        fname, ftype = QFileDialog.getOpenFileName(self, '发送文件', CUR_PATH,
                                                   "All files (*)")
        # print(fname, "->", ftype)
        if fname:
            _data = None
            with open(fname, "rb") as f:
                _data = f.read()
            # print(type(_data))
            if not self._serial.isOpen():
                QMessageBox.warning(self, "警告", "串口未打开!", QMessageBox.Yes)
                return
            if not _data:
                QMessageBox.warning(self, "警告", "没有发送数据!", QMessageBox.Yes)
                return
            _num = self._serial.write(_data)
            self._num_send += _num
            self._label_num_send.setText("发送:" + str(self._num_send))

    def closeEvent(self, event):
        # 重载关闭窗口事件
        self._timer_one_s.stop()
        if self._serial.isOpen():
            self._serial.close()
        super(Serial, self).closeEvent(event)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    satrtwindow = Serial()
    satrtwindow.show()
    sys.exit(app.exec_())
