#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include <iostream>
#include "Position.hpp"
#include "Solver.hpp"

namespace py = pybind11;
using namespace GameSolver::Connect4;

PYBIND11_MODULE(connect4, m) {
    m.doc() = "Python bindings for Connect4 Game Solver";

    py::class_<Position>(m, "Position")
        .def(py::init<>())
        .def(py::init([](py::array_t<int> board, int current_player = 1) {
            if (board.ndim() != 2) {
                throw std::runtime_error("Board must be a 2D array");
            }
            if (board.shape(0) != Position::HEIGHT || board.shape(1) != Position::WIDTH) {
                throw std::runtime_error("Board must be 6x7");
            }
            auto r = board.unchecked<2>();
            int board_array[Position::HEIGHT][Position::WIDTH];
            for (int i = 0; i < Position::HEIGHT; i++) {
                for (int j = 0; j < Position::WIDTH; j++) {
                    board_array[i][j] = r(i, j);
                }
            }
            return new Position(board_array, current_player);
        }), py::arg("board"), py::arg("current_player") = 1)
        .def("play", (void (Position::*)(Position::position_t)) &Position::play)
        .def("play", (unsigned int (Position::*)(const std::string&)) &Position::play)
        .def("can_win_next", &Position::canWinNext)
        .def("nb_moves", &Position::nbMoves)
        .def("key", &Position::key)
        .def("key3", &Position::key3)
        .def("possible_non_losing_moves", &Position::possibleNonLosingMoves)
        .def("can_play", &Position::canPlay)
        .def("play_col", &Position::playCol)
        .def("is_winning_move", &Position::isWinningMove)
        .def("draw", &Position::draw)
        .def("get_board", [](const Position& pos) {
            auto board = pos.get_board();
            // Create a NumPy array with the same shape and data
            py::array_t<int> result({Position::HEIGHT, Position::WIDTH});
            auto r = result.mutable_unchecked<2>();
            for (int i = 0; i < Position::HEIGHT; i++) {
                for (int j = 0; j < Position::WIDTH; j++) {
                    r(i, j) = board[i][j];
                }
            }
            return result;
        })
        .def_readonly_static("WIDTH", &Position::WIDTH)
        .def_readonly_static("HEIGHT", &Position::HEIGHT)
        .def_readonly_static("MIN_SCORE", &Position::MIN_SCORE)
        .def_readonly_static("MAX_SCORE", &Position::MAX_SCORE);

    py::class_<Solver>(m, "Solver")
        .def(py::init<>())
        .def("solve", &Solver::solve)
        .def("analyze", &Solver::analyze)
        .def_static("evaluate_score", &Solver::evaluate_score);
}

